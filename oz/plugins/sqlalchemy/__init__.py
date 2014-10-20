from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from multiprocessing.util import register_after_fork
import tornado.options
import oz
import oz.app

from .actions import *
from .middleware import *
from .options import *

Base = declarative_base()
_engine = None
_session = None

class _AfterFork(object):
    registered = False

    def __call__(self):
        global _engine
        global _session

        # Child must reregister
        self.registered = False

        _engine.dispose()
        _engine = None
        _session = None

after_fork = _AfterFork()

def setup():
    """Initializes the tables if they don't exist already"""
    return Base.metadata.create_all(engine())

def engine():
    global _engine

    if _engine == None:
        kwargs = dict(echo=oz.app.settings["debug_sql"])

        if oz.app.settings["db_pool_size"]:
            kwargs["pool_size"] = oz.app.settings["db_pool_size"]
        if oz.app.settings["db_max_overflow"]:
            kwargs["max_overflow"] = oz.app.settings["db_max_overflow"]
        if oz.app.settings["db_pool_timeout"]:
            kwargs["pool_timeout"] = oz.app.settings["db_pool_timeout"]

        _engine = create_engine(oz.app.settings["db"], **kwargs)
        after_fork.registered = True
        register_after_fork(after_fork, after_fork)

    return _engine

def session():
    """Gets a SQLAlchemy session"""
    global _session

    if _session == None:
        _session = sessionmaker(bind=engine())

    return _session()
