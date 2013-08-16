from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.app
import oz.plugins.redis_sessions

class RedisSessionMiddleware(object):
    def _session_key(self):
        """Gets the redis key for a session"""

        session_id = self.get_cookie("session_id")

        # Generate a new session if one does not exist yet
        if session_id == None:
            session_id = oz.plugins.redis_sessions.random_hex(20)
            self.set_cookie("session_id", session_id, httponly=True)

        password_salt = oz.app.settings["session_salt"]
        return "session:%s:v2" % oz.plugins.redis_sessions.password_hash(password_salt, session_id)

    def _update_session_expiration(self):
        """
        Updates a redis item to expire later since it has been interacted with
        recently
        """

        session_time = oz.app.settings["session_time"]

        if session_time:
            self.redis().expire(self._session_key(), session_time)

    def get_session_value(self, name, default=None):
        """Gets a session value"""

        value = self.redis().hget(self._session_key(), name) or default
        self._update_session_expiration()
        return value

    def set_session_value(self, name, value):
        """Sets a session value"""

        self.redis().hset(self._session_key(), name, value)
        self._update_session_expiration()

    def clear_session_value(self, name):
        """Removes a session value"""
        self.redis().hdel(self._session_key(), name)
        self._update_session_expiration()

    def clear_all_session_values(self):
        """Kills a session"""
        self.redis().delete(self._session_key())
        self.clear_cookie("session_id")
