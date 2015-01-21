"""The redis plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import redis

from .middleware import *
from .options import *

_cached_connection = None

def create_connection():
    """Sets up a redis configuration"""

    global _cached_connection
    settings = oz.settings

    if settings["redis_cache_connections"] and _cached_connection != None:
        return _cached_connection
    else:
        conn = redis.StrictRedis(
            host=settings["redis_host"],
            port=settings["redis_port"],
            db=settings["redis_db"],
            password=settings["redis_password"],
            decode_responses=settings["redis_decode_responses"],
        )

        if settings["redis_cache_connections"]:
            _cached_connection = conn

        return conn
