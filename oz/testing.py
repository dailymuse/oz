"""Tools for running unit tests"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import tornado.web
import tornado.testing
import oz
import collections

# Pseudo-cookie storage
cookie_counter = 0
cookie_jar = collections.defaultdict(lambda: {})

# Pseudo-redis storage
redis_collection = collections.defaultdict(lambda: {})

class OzTestCase(tornado.testing.AsyncHTTPTestCase):
    """
    Base class for web tests that use the oz infrastructure. Override
    get_handlers to specify the endpoints used in the test.
    """

    forced_settings = {}

    def setUp(self):
        super(OzTestCase, self).setUp()

        self.old_settings = oz.settings

        new_settings = dict(oz.settings)
        new_settings.update(self.forced_settings)
        oz.settings = new_settings

    def tearDown(self):
        super(OzTestCase, self).tearDown()
        oz.settings = self.old_settings

    def get_app(self):
        self.app = tornado.web.Application(self.get_handlers(), **oz.settings)
        return self.app

    def get_handlers(self):
        """Specifies what routes to expose for this test"""
        raise NotImplementedError()

    def request(self, path, **kwargs):
        """Makes a request to one of the routes exposed by this test"""
        self.http_client.fetch(self.get_url(path), self.stop, **kwargs)
        return self.wait()

class FakeCookiesHandler(oz.RequestHandler):
    """
    A request handler that has a pseudo-cookie storage engine. Used because
    the HTTP client used for tornado unit testing doesn't persist cookies
    across requests.
    """

    def initialize(self, *args, **kwargs):
        super(FakeCookiesHandler, self).initialize(*args, **kwargs)
        self.__cookie_id = None

    @property
    def _cookie_id(self):
        """
        The cookie ID associated with this request. This value will be unique
        for the request.
        """

        if not self.__cookie_id:
            # Generate a cookie ID if one hasn't been made yet
            self.__cookie_id = self.get_argument("cookie_id", None)

            if not self.__cookie_id:
                global cookie_counter
                self.__cookie_id = cookie_counter
                cookie_counter += 1

        return self.__cookie_id

    @property
    def cookies(self):
        return cookie_jar[self._cookie_id]

    def get_cookie(self, name, default=None):
        return cookie_jar[self._cookie_id].get(name, default)

    def set_cookie(self, name, value, **kwargs):
        cookie_jar[self._cookie_id][name] = value

    def clear_cookie(self, name):
        del cookie_jar[self._cookie_id][name]

    def clear_all_cookies(self):
        cookie_jar[self._cookie_id] = {}
