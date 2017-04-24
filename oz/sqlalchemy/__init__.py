"""The sqlalchemy plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from multiprocessing.util import register_after_fork
import oz

from .actions import *
from .middleware import *
from .options import *

Base = declarative_base()
_engines = dict()
_session_makers = dict()

class _AfterFork(object):
    """
    Ensures cleanup of sqlalchemy connections after a fork is done. This guard
    is here because sqlalchemy connections cannot be shared across processes.
    """

    registered = False

    def __call__(self):
        global _engines
        global _session_makers

        # Child must reregister
        self.registered = False

        for engine in _engines.values():
            engine.dispose()

        _engines = dict()
        _session_makers = dict()

after_fork = _AfterFork()

def setup(connection_string=None):
    """Initializes the tables if they don't exist already"""
    return Base.metadata.create_all(engine(connection_string=connection_string))

def engine(connection_string=None):
    global _engines
    connection_string = connection_string or oz.settings["db"]

    if connection_string not in _engines:
        kwargs = dict(echo=oz.settings["debug_sql"])

        if oz.settings["db_pool_size"]:
            kwargs["pool_size"] = oz.settings["db_pool_size"]
        if oz.settings["db_max_overflow"]:
            kwargs["max_overflow"] = oz.settings["db_max_overflow"]
        if oz.settings["db_pool_timeout"]:
            kwargs["pool_timeout"] = oz.settings["db_pool_timeout"]

        first_engine = len(_engines) == 0
        _engines[connection_string] = create_engine(connection_string, **kwargs)

        if first_engine:
            after_fork.registered = True
            register_after_fork(after_fork, after_fork)

    return _engines[connection_string]

def session(connection_string=None):
    """Gets a SQLAlchemy session"""
    global _session_makers
    connection_string = connection_string or oz.settings["db"]

    if not connection_string in _session_makers:
        _session_makers[connection_string] = sessionmaker(bind=engine(connection_string=connection_string))

    return _session_makers[connection_string]()
