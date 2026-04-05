from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
import sqlite3
import database.models
import configparser
import logging

_logger: logging.Logger
_config: configparser.ConfigParser
_engine = None
_session = None

def init(config):
    global _logger, _config, _engine, _session
    _logger = logging.getLogger(__name__)
    _config = configparser.ConfigParser()
    _config.read("config.ini")
    connection_string: str = _config["connection_strings"]["default"]
    print(connection_string)
    _logger.debug(f"Connection string: {connection_string}")
    _engine = create_engine(connection_string)

    #Create database tables if they do not exist.
    #NOTE - does not update tables if columns change.
    database.models.Base.metadata.create_all(_engine)
    _session = Session(_engine)

    try:
        print("DbTest")
        result = _session.execute(text("SELECT * FROM 'quotes';"))
        print(result.all())
    except BaseException as e:
        _logger.error(f"Could not initialize DbConnection: {e}")

def get_table_rows(table):
    try:
        rows = _session.query(table).all()
        return rows
    except BaseException as e:
        _logger.error(f"Failed to get items from database table {table}: {e}")
    return None

def add_row(obj: any):
    try:
        _session.add(obj)
        _session.commit()
        return True
    except BaseException as e:
        _logger.error(f"Failed to add item {obj} to database: {e}")
    return False
    

def cleanup():
    try:
        _session.close()
        _engine.dispose()
    except BaseException as e:
        print(e)