from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import collections
import oz.plugins.redis
from oz.plugins.aws_cdn import CDNMiddleware
from oz.plugins.redis import RedisMiddleware

@oz.test
class CDNMiddlewareTest(oz.testing.OzTestCase):
    forced_settings = {
        "static_host": "//fakecdn"
    }

    def get_handlers(self):
        class CDNHandler(oz.RequestHandler, RedisMiddleware, CDNMiddleware):
            def put(self):
                file, value = self.request.body.split(":")
                self.set_cache_buster(file, value)
                self.finish("ok")

        class CacheBusterHandler(CDNHandler):
            def get(self):
                self.finish(self.get_cache_buster(self.get_argument("file")))

        class StaticUrlHandler(CDNHandler):
            def get(self):
                self.finish(self.cdn_static_url(self.get_argument("file")))

        return [
            ("/cache_buster", CacheBusterHandler),
            ("/static_url", StaticUrlHandler),
        ]

    def tearDown(self):
        super(CDNMiddlewareTest, self).tearDown()

        # Kill the created key
        redis = oz.plugins.redis.create_connection()
        redis.delete("cache-buster:v1")

    def test_get_cache_buster(self):
        self.http_client.fetch(self.get_url("/cache_buster"), self.stop, method="PUT", body="path/to/file.txt:abcdef")
        response = self.wait()
        self.assertEqual(response.body, "ok")

        self.http_client.fetch(self.get_url("/cache_buster?file=path%2Fto%2Ffile.txt"), self.stop)
        response = self.wait()
        self.assertEqual(response.body, "abcdef")

    def test_static_url(self):
        self.http_client.fetch(self.get_url("/static_url"), self.stop, method="PUT", body="path/to/file2.txt:ghijkl")
        response = self.wait()
        self.assertEqual(response.body, "ok")

        self.http_client.fetch(self.get_url("/static_url?file=path%2Fto%2Ffile2.txt"), self.stop)
        response = self.wait()
        self.assertEqual(response.body, "//fakecdn/path/to/file2.txt?v=ghijkl")
