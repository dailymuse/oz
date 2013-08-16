from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.plugins.sqlalchemy

class SQLAlchemyMiddleware(object):
    def __init__(self):
        super(SQLAlchemyMiddleware, self).__init__()
        self.trigger_listener("on_finish", self._sqlalchemy_on_finish)

    def db(self):
        """Gets the SQLALchemy session for this request"""

        if not hasattr(self, "db_conn"):
            self.db_conn = oz.plugins.sqlalchemy.session()

        return self.db_conn

    def _sqlalchemy_on_finish(self):
        # Close the SQLAlchemy session
        if hasattr(self, "db_conn"):
            if self.get_status() >= 200 and self.get_status() <= 399:
                self.db_conn.commit()
            else:
                self.db_conn.rollback()

            self.db_conn.close()
