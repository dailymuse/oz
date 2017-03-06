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

    def db(self):
        """Gets the SQLALchemy session for this request"""

        if not hasattr(self, "db_conn"):
            self.db_conn = oz.sqlalchemy.session()

        return self.db_conn

    def _sqlalchemy_on_finish(self):
        """
        Closes the sqlalchemy transaction. Rolls back if an error occurred.
        """

        if hasattr(self, "db_conn"):
            try:
                if self.get_status() >= 200 and self.get_status() <= 399:
                    self.db_conn.commit()
                else:
                    self.db_conn.rollback()
            except:
                tornado.log.app_log.warning("Error occurred during database transaction cleanup: %s", str(sys.exc_info()[0]))
                raise
            finally:
                self.db_conn.close()

    def _sqlalchemy_on_connection_close(self):
        """
        Rollsback and closes the active session, since the client disconnected before the request
        could be completed.
        """

        if hasattr(self, "db_conn"):
            try:
                self.db_conn.rollback()
            except:
                tornado.log.app_log.warning("Error occurred during database transaction cleanup: %s", str(sys.exc_info()[0]))
                raise
            finally:
                self.db_conn.close()
