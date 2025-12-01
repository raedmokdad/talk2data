# core/sql_connectors.py
from __future__ import annotations
from typing import Any, Dict, List
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from .base_connector import BaseConnector
from .models import DBSelection, DBType


class SQLAlchemyConnector(BaseConnector):
    """
    Connector implementation using SQLAlchemy for SQL DBs:
    Postgres, MySQL, Redshift.
    """

    def __init__(self, engine: Engine, db_type: DBType):
        self.engine = engine
        self.db_type = db_type

    def test_connection(self) -> bool:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True

    def run_query(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            cols = result.keys()
            rows = [dict(zip(cols, row)) for row in result.fetchall()]
        return rows

    def execute(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(sql), params or {})

    def list_tables(self) -> List[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        inspector = inspect(self.engine)
        cols = inspector.get_columns(table_name)
        return [
            {
                "name": c["name"],
                "type": str(c["type"]),
                "nullable": bool(c.get("nullable", True)),
                "default": c.get("default"),
            }
            for c in cols
        ]


def build_sqlalchemy_engine(selection: DBSelection) -> Engine:
    if selection.db_type == DBType.POSTGRES:
        driver = "postgresql+psycopg2"
        default_port = 5432
    elif selection.db_type == DBType.MYSQL:
        driver = "mysql+pymysql"
        default_port = 3306
    elif selection.db_type == DBType.REDSHIFT:
        driver = "postgresql+psycopg2"  # Redshift is Postgres-compatible
        default_port = 5439
    else:
        raise ValueError(f"Unsupported DB type for SQLAlchemy: {selection.db_type}")

    port = selection.port or default_port

    url = (
        f"{driver}://{selection.user}:{selection.password}"
        f"@{selection.host}:{port}/{selection.database}"
    )
    
    # Für PostgreSQL mit deutschen Locale (lc_messages = German_Germany.1252):
    # Fehlermeldungen kommen in Windows-1252, daher client_encoding auf WIN1252 setzen
    connect_args = {}
    if selection.db_type in (DBType.POSTGRES, DBType.REDSHIFT):
        connect_args = {"options": "-c client_encoding=WIN1252"}

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args,
    )
    return engine
