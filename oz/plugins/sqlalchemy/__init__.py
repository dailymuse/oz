from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import tornado.options
import oz
import oz.app

from .actions import *
from .middleware import *
from .options import *

Base = declarative_base()
engine = None
Session = None

@oz.signal("initialized")
def initialize(pool_timeout=None):
    """Initializes a new SQLAlchemy environment"""

    global engine, Session

    kwargs = { "echo": oz.app.settings["debug_sql"] }
    if pool_timeout != None: kwargs["pool_timeout"] = pool_timeout

    engine = create_engine(oz.app.settings["db"], **kwargs)
    Session = sessionmaker(bind=engine)

def setup():
    """Initializes the tables if they don't exist already"""
    return Base.metadata.create_all(engine)

def session():
    """Gets a SQLAlchemy session"""
    global Session
    assert Session != None, "SQLAlchemy has not been initialized"
    return Session()
