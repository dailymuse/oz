"""Middleware for the sqlalchemy plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import sys

import tornado.log

import oz
import oz.sqlalchemy

class SQLAlchemyMiddleware(object):
    """Adds a per-request sqlalchemy transaction"""

    def __init__(self):
        super(SQLAlchemyMiddleware, self).__init__()
        self.trigger_listener("on_finish", self._sqlalchemy_on_finish)
        self.trigger_listener("on_connection_close", self._sqlalchemy_on_connection_close)

    def db(self, connection_string=None):
        """Gets the SQLALchemy session for this request"""

        connection_string = connection_string or self.settings["db"]

        if not hasattr(self, "_db_conns"):
            self._db_conns = {}
        if not connection_string in self._db_conns:
            self._db_conns[connection_string] = oz.sqlalchemy.session(connection_string=connection_string)

        return self._db_conns[connection_string]

    def _sqlalchemy_on_finish(self):
        """
        Closes the sqlalchemy transaction. Rolls back if an error occurred.
        """

        if hasattr(self, "_db_conns"):
            try:
                if self.get_status() >= 200 and self.get_status() <= 399:
                    for db_conn in self._db_conns.values():
                        db_conn.commit()
                else:
                    for db_conn in self._db_conns.values():
                        db_conn.rollback()
            except:
                tornado.log.app_log.warning("Error occurred during database transaction cleanup: %s", str(sys.exc_info()[0]))
                raise
            finally:
                for db_conn in self._db_conns.values():
                    try:
                        db_conn.close()
                    except:
                        tornado.log.app_log.warning("Error occurred when closing the database connection", exc_info=True)

    def _sqlalchemy_on_connection_close(self):
        """
        Rollsback and closes the active session, since the client disconnected before the request
        could be completed.
        """

        if hasattr(self, "_db_conns"):
            try:
                for db_conn in self._db_conns.values():
                    db_conn.rollback()
            except:
                tornado.log.app_log.warning("Error occurred during database transaction cleanup: %s", str(sys.exc_info()[0]))
                raise
            finally:
                for db_conn in self._db_conns.values():
                    try:
                        db_conn.close()
                    except:
                        tornado.log.app_log.warning("Error occurred when closing the database connection", exc_info=True)
