from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.redis

class RedisMiddleware(object):
    def redis(self):
        """Gets or creates a connection to the redis database"""
        return oz.redis.create_connection()