# core/factory.py
from __future__ import annotations
from .models import DBSelection, DBType
from .base_connector import BaseConnector
from .sql_connectors import SQLAlchemyConnector, build_sqlalchemy_engine
from .file_connectors import FileConnector


def create_connector(selection: DBSelection) -> BaseConnector:
    """
    Given a DBSelection, create and return a ready-to-use connector.
    """

    if selection.db_type in {DBType.POSTGRES, DBType.MYSQL, DBType.REDSHIFT}:
        engine = build_sqlalchemy_engine(selection)
        connector = SQLAlchemyConnector(engine, selection.db_type)
        connector.test_connection()
        return connector

    if selection.db_type == DBType.FILES:
        if not selection.files:
            raise ValueError("No files provided for FILES db_type")
        connector = FileConnector(selection.files)
        connector.test_connection()
        return connector

    raise ValueError(f"Unsupported db_type: {selection.db_type}")
