"""Options for the redis plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    redis_cache_connections = dict(type=bool, default=True, help="Whether to cache the redis connection between requests to prevent TCP slow start"),
    redis_host = dict(type=str, default="localhost", help="Redis host"),
    redis_port = dict(type=int, default=6379, help="Redis port"),
    redis_db = dict(type=int, default=0, help="Redis database number"),
    redis_password = dict(type=str, default=None, help="Password to the redis database"),
    redis_decode_responses = dict(type=bool, default=False, help="Whether to decode redis responses automatically. Keep this False if you're handling binary data in redis."),
)