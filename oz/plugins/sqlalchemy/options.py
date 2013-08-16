from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    db = dict(type=str, help="SQLAlchemy connection string to the database"),
    debug_sql = dict(type=bool, default=False, help="Dump SQL queries performed by SQLAlchemy to stdout"),
)