from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import os
import oz
import oz.testing
import collections
import oz.redis
from oz.aws_cdn import CDNMiddleware
from tornado import escape, web

@oz.test
class CDNMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "static_host": "//fakecdn",
        "static_path": "static"
    }

    def get_handlers(self):
        class CDNHandler(oz.RequestHandler, oz.redis.RedisMiddleware, CDNMiddleware):
            pass

        class CacheBusterHandler(CDNHandler):
            def get(self, f):
                self.finish(self.get_cache_buster(f))

            def put(self, f):
                self.set_cache_buster(f, self.get_argument("value"))

        class StaticUrlHandler(CDNHandler):
            def get(self, f):
                self.finish(self.cdn_static_url(f))

        class GetFileHandler(CDNHandler):
            def get(self, path):
                # Gets the contents of a file
                f = self.get_file(path)

                if not f.exists():
                    raise web.HTTPError(404)

                self.finish(f.contents())

            def put(self, path):
                # Sets the contents of a file to the request body
                replace = self.get_argument("replace") == "true"
                self.upload_file(path, escape.utf8(self.request.body), replace=replace)

        class CopyFileHandler(CDNHandler):
            def put(self, from_path, to_path):
                # Copies a file from one path to another
                replace = self.get_argument("replace") == "true"
                self.copy_file(from_path, to_path, replace=replace)

        return [
            (r"^/cache-buster/(.+)$", CacheBusterHandler),
            (r"^/static-url/(.+)$", StaticUrlHandler),
            (r"^/file/([^/]+)$", GetFileHandler),
            (r"^/copy-file/([^/]+)/([^/]+)$", CopyFileHandler),
        ]

    def tearDown(self):
        super(CDNMiddlewareTestCase, self).tearDown()

        # Kill the created key
        redis = oz.redis.create_connection()
        redis.delete("cache-buster:v2")

        # Kill any test files
        for f in os.listdir("static"):
            if f.startswith("test-aws-cdn-"):
                os.remove(os.path.join("static", f))

    def test_get_cache_buster(self):
        # Set a cache buster
        response = self.request("/cache-buster/get-cache-buster-example?value=abcdef", method="PUT", body="")
        self.assertEqual(response.code, 200)

        # Check the results are OK
        response = self.request("/cache-buster/get-cache-buster-example")
        self.assertEqual(response.body, b"abcdef")

        # Get a non-existent cache buster
        response = self.request("/cache-buster/non-existent")
        self.assertEqual(response.body, b"")

    def test_static_url(self):
        response = self.request("/static-url/static-url-example")
        self.assertEqual(response.body, b"//fakecdn/static-url-example?v=None")

    def set_file(self, name, contents, replace=False):
        replace_str = "true" if replace else False
        response = self.request("/file/test-aws-cdn-%s?replace=%s" % (name, replace_str), method="PUT", body=contents)
        self.assertEqual(response.code, 200)

    def get_file(self, name):
        response = self.request("/file/test-aws-cdn-%s" % name)
        self.assertEqual(response.code, 200)
        return response.body

    def copy_file(self, from_path, to_path, replace=False):
        replace_str = "true" if replace else False
        response = self.request("/copy-file/test-aws-cdn-%s/test-aws-cdn-%s?replace=%s" % (from_path, to_path, replace_str), method="PUT", body="")
        self.assertEqual(response.code, 200)

    def test_get_file(self):
        # Get a non-existent file
        response = self.request("/file/unreal")
        self.assertEqual(response.code, 404)

        # Set a file 3 times
        self.set_file("get-file-example", "Hello, world!", replace=False)
        self.set_file("get-file-example", "Hello, world 2!", replace=True)
        self.set_file("get-file-example", "Hello, world 3!", replace=False)

        # Get the new file
        self.assertEqual(self.get_file("get-file-example"), b"Hello, world 2!")

    def test_copy_file(self):
        # Set a baseline files
        self.set_file("copy-file-baseline-1", "Hello, world!", replace=False)
        self.set_file("copy-file-baseline-2", "Hello, world 2!", replace=False)
        self.set_file("copy-file-baseline-3", "Hello, world 3!", replace=False)

        # Copy the file
        self.copy_file("copy-file-baseline-1", "copy-file-example", replace=False)
        self.copy_file("copy-file-baseline-2", "copy-file-example", replace=True)
        self.copy_file("copy-file-baseline-3", "copy-file-example", replace=False)

        # Check that the file was copied correctly
        self.assertEqual(self.get_file("copy-file-example"), b"Hello, world 2!")
