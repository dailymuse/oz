"""Options for the sqlalchemy plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    db = dict(type=str, help="SQLAlchemy connection string to the database"),
    debug_sql = dict(type=bool, default=False, help="Dump SQL queries performed by SQLAlchemy to stdout"),
    db_pool_size = dict(type=int, default=None, help="Size of the SQLAlchemy connection pool"),
    db_max_overflow = dict(type=int, default=None, help="How many extra transient connections can be put in the SQLAlchemy connection pool if needed"),
    db_pool_timeout = dict(type=int, default=None, help="Number of seconds to wait before a SQLAlchemy connection is returned to the pool"),
)