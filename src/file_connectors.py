from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import re

import duckdb
import pandas as pd

from .base_connector import BaseConnector
from .models import FileItem, FileType


def sanitize_table_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return name or "table"


class FileConnector(BaseConnector):
    """
    Connector for multiple CSV/Excel files.
    Supports:
      - Local paths (path)
      - S3 URIs (s3_uri) for CSV & Excel
    """

    def __init__(self, files: List[FileItem]):
        self.con = duckdb.connect(database=":memory:")
        self.table_names: List[str] = []

        for file_item in files:
            # If something came as dict from Pydantic or Streamlit, convert it
            if isinstance(file_item, dict):
                file_item = FileItem(**file_item)

            table_name = self._register_file(file_item)
            self.table_names.append(table_name)

    def _register_file(self, file_item: FileItem) -> str:
        """
        Register a single file (CSV or EXCEL) as a DuckDB table/view.
        """
        if file_item.s3_uri:
            # Name from S3 key
            name_stem = file_item.s3_uri.split("/")[-1].split(".")[0]
        elif file_item.path:
            name_stem = Path(file_item.path).stem
        else:
            raise ValueError("FileItem must have either path or s3_uri")

        table_name = sanitize_table_name(name_stem)

        # CSV handling
        if file_item.type == FileType.CSV:
            if file_item.s3_uri:
                # DuckDB can read CSV directly from S3
                self.con.execute(
                    f"""
                    CREATE VIEW {table_name} AS
                    SELECT * FROM read_csv_auto('{file_item.s3_uri}')
                    """
                )
            elif file_item.path:
                self.con.execute(
                    f"""
                    CREATE VIEW {table_name} AS
                    SELECT * FROM read_csv_auto('{Path(file_item.path).as_posix()}')
                    """
                )
            else:
                raise ValueError("CSV file must have path or s3_uri")

        # EXCEL handling
        elif file_item.type == FileType.EXCEL:
            # For Excel, DuckDB doesn't read .xlsx directly:
            # Use pandas.read_excel, supporting s3:// via s3fs, then register DF.
            if file_item.s3_uri:
                excel_source = file_item.s3_uri
            elif file_item.path:
                excel_source = Path(file_item.path).as_posix()
            else:
                raise ValueError("Excel file must have path or s3_uri")

            if file_item.sheet_name:
                df = pd.read_excel(
                    excel_source,
                    sheet_name=file_item.sheet_name,
                )
            else:
                df = pd.read_excel(excel_source)

            if isinstance(df, dict):
                # If multiple sheets returned, take the first sheet by default
                df = next(iter(df.values()))

            if not isinstance(df, pd.DataFrame):
                raise TypeError(
                    f"Expected pandas.DataFrame, got {type(df)} for {table_name}"
                )

            self.con.register(table_name, df)

        else:
            raise ValueError(f"Unsupported file type: {file_item.type}")

        return table_name

    # ---- BaseConnector methods ----

    def test_connection(self) -> bool:
        if not self.table_names:
            raise ValueError("No tables registered")
        t = self.table_names[0]
        self.con.execute(f"SELECT 1 FROM {t} LIMIT 1")
        return True

    def run_query(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        result = self.con.execute(sql)
        cols = [d[0] for d in result.description]
        rows = result.fetchall()
        return [dict(zip(cols, r)) for r in rows]

    def execute(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> None:
        self.con.execute(sql)

    def list_tables(self) -> List[str]:
        return list(self.table_names)

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        res = self.con.execute(f"DESCRIBE {table_name}").fetchall()
        return [
            {"name": r[0], "type": r[1], "nullable": bool(r[2])}
            for r in res
        ]
