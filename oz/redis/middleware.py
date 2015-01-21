"""Middleware for the redis plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.redis

class RedisMiddleware(object):
    """Adds a redis connection to the RequestHandler"""

    def redis(self):
        """Gets or creates a connection to the redis database"""
        return oz.redis.create_connection()
