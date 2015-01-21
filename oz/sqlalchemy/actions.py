"""Actions for the sqlalchemy plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.sqlalchemy

@oz.action
def setup_database():
    """Sets up the database tables"""
    oz.sqlalchemy.setup()
