"""The sqlalchemy plugin."""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from multiprocessing.util import register_after_fork

from sqlalchemy import create_engine, exc, event, select
from sqlalchemy import __version__ as sa_version
from sqlalchemy.engine import Engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import oz

from .actions import *
from .middleware import *
from .options import *

Base = declarative_base()
_engines = dict()
_session_makers = dict()


def _ping_connection(connection, branch):
    if branch:
        # "branch" refers to a sub-connection of a connection,
        # we don't want to bother pinging on these.
        return

    # turn off "close with result".  This flag is only used with
    # "connectionless" execution, otherwise will be False in any case
    save_should_close_with_result = connection.should_close_with_result
    connection.should_close_with_result = False

    try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        connection.scalar(select([1]))
    except exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
        if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            connection.scalar(select([1]))
        else:
            raise
    finally:
        # restore "close with result"
        connection.should_close_with_result = save_should_close_with_result


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
        if oz.settings["db_pool_pre_ping"]:
            major, minor, *patch = sa_version.split(".")
            major = int(major)
            minor = int(minor)
            if patch:
                patch, *_ = patch[0].split("b")
                patch = int(patch)
            else:
                patch = None

            # Do not cast patch, as it could be beta/alpha .. may not even exist.
            if major > 1 and (minor > 2 or (minor == 2 and patch and patch >= 3)):
                # We can use the native pool_pre_ping
                kwargs["pool_pre_ping"] = oz.settings["db_pool_pre_ping"]
            else:
                # We are on an old version of pg. Use the event-based
                # pre-ping
                event.listen(Engine, "engine_connect", _ping_connection)

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


