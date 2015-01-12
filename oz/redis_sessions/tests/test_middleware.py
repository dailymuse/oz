from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import collections
from oz.redis_sessions import RedisSessionMiddleware
from oz.redis import RedisMiddleware

@oz.test
class RedisSessionMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "session_salt": "abc",
        "session_time": 60 * 1000
    }

    def get_handlers(self):
        class SessionGetterHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware):
            def get(self):
                self.finish(self.get_session_value(self.get_argument("name"), self.get_argument("default", None)))

        class SessionSetterHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware):
            def get(self):
                self.finish(self.set_session_value(self.get_argument("name"), self.get_argument("value")))

        class SessionDeleterHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware):
            def get(self):
                self.finish(self.clear_session_value(self.get_argument("name")))

        class SessionClearerHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware):
            def get(self):
                self.clear_all_session_values()

        return [
            ("/get", SessionGetterHandler),
            ("/set", SessionSetterHandler),
            ("/del", SessionDeleterHandler),
            ("/clear", SessionClearerHandler),
        ]

    def tearDown(self):
        super(RedisSessionMiddlewareTestCase, self).tearDown()
        
        # Clean up just in case there's keys still lying around
        redis = oz.redis.create_connection()

        for key in redis.keys("session:*:v1"):
            redis.delete(key)

    def test_session_value(self):
        response = self.request("/set?name=session_value_1&value=bar&cookie_id=test_session_value")
        self.assertEqual(response.body, b"")

        response = self.request("/get?name=session_value_1&cookie_id=test_session_value")
        self.assertEqual(response.body, b"bar")

        response = self.request("/get?name=session_value_2&cookie_id=test_session_value")
        self.assertEqual(response.body, b"")

        response = self.request("/get?name=session_value_2&default=bar2&cookie_id=test_session_value")
        self.assertEqual(response.body, b"bar2")

    def test_clear_session_value(self):
        response = self.request("/set?name=clearable_value&value=baz&cookie_id=test_clear_session_value")
        self.assertEqual(response.body, b"")

        response = self.request("/del?name=clearable_value&cookie_id=test_clear_session_value")
        self.assertEqual(response.body, b"")

        response = self.request("/get?name=clearable_value&cookie_id=test_clear_session_value")
        self.assertEqual(response.body, b"")

    def test_clear_all_session_values(self):
        response = self.request("/set?name=clear_all_value_1&value=baz&cookie_id=test_clear_all_session_values")
        self.assertEqual(response.body, b"")

        response = self.request("/set?name=clear_all_value_2&value=baz&cookie_id=test_clear_all_session_values")
        self.assertEqual(response.body, b"")

        response = self.request("/clear?cookie_id=test_clear_all_session_values")
        self.assertEqual(response.body, b"")

        response = self.request("/get?name=clear_all_value_1&cookie_id=test_clear_all_session_values")
        self.assertEqual(response.body, b"")

        response = self.request("/get?name=clear_all_value_2&cookie_id=test_clear_all_session_values")
        self.assertEqual(response.body, b"")
