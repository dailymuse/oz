"""Middleware for the redis sessions plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.redis_sessions

class RedisSessionMiddleware(object):
    """Adds redis-backed session capabilities"""

    @property
    def _session_key(self):
        """Gets the redis key for a session"""

        if not hasattr(self, "_cached_session_key"):
            session_id_bytes = self.get_secure_cookie("session_id")
            session_id = None

            if session_id_bytes:
                try:
                    session_id = session_id_bytes.decode('utf-8')
                except:
                    pass

            if not session_id:
                session_id = oz.redis_sessions.random_hex(20)
                self.set_secure_cookie("session_id", session_id.encode('utf-8'), httponly=True)

            password_salt = oz.settings["session_salt"]
            self._cached_session_key = "session:%s:v4" % oz.redis_sessions.password_hash(session_id, password_salt=password_salt)
        
        return self._cached_session_key

    def _update_session_expiration(self):
        """
        Updates a redis item to expire later since it has been interacted with
        recently
        """

        session_time = oz.settings["session_time"]

        if session_time:
            self.redis().expire(self._session_key, session_time)

    def get_session_value(self, name, default=None):
        """Gets a session value"""

        value = self.redis().hget(self._session_key, name) or default
        self._update_session_expiration()
        return value

    def set_session_value(self, name, value):
        """Sets a session value"""

        self.redis().hset(self._session_key, name, value)
        self._update_session_expiration()

    def clear_session_value(self, name):
        """Removes a session value"""
        self.redis().hdel(self._session_key, name)
        self._update_session_expiration()

    def clear_all_session_values(self):
        """Kills a session"""
        self.redis().delete(self._session_key)
        self.clear_cookie("session_id")
