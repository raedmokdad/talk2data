from __future__ import annotations
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator, FieldValidationInfo


class DBType(str, Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    REDSHIFT = "redshift"
    FILES = "files"


class FileType(str, Enum):
    CSV = "csv"
    EXCEL = "excel"


class FileItem(BaseModel):
    path: Optional[str] = None
    s3_uri: Optional[str] = None  # s3://bucket/key.xlsx

    type: FileType
    sheet_name: Optional[str] = None
    table_name: Optional[str] = None  # Override table name (default: filename stem)


class DBSelection(BaseModel):

    """
    Represents the user’s selection.
    For SQL DBs: use connection fields.
    For FILES: use `files`.
    """

    db_type: DBType

    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    files: Optional[List[FileItem]] = Field(default=None)

    @field_validator("host", "port", "database", "user", "password")
    @classmethod
    def validate_sql_fields(cls, v, info: FieldValidationInfo):
        db_type = info.data.get("db_type")
        if db_type in {DBType.POSTGRES, DBType.MYSQL, DBType.REDSHIFT}:
            if v is None:
                raise ValueError(f"{info.field_name} is required for SQL databases")
        return v

    @model_validator(mode="after")
    def validate_files_for_files_db(self) -> "DBSelection":
        if self.db_type == DBType.FILES:
            if not self.files or len(self.files) == 0:
                raise ValueError("At least one file is required for FILES db_type")
        return self

