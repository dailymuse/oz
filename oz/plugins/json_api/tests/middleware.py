from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import oz.plugins.json_api
from oz.plugins.json_api import ApiMiddleware
import tornado.escape

class ApiMiddlewareTestHandler(oz.RequestHandler, ApiMiddleware):
    def initialize(self, *args, **kwargs):
        super(ApiMiddlewareTestHandler, self).initialize(*args, **kwargs)

@oz.test
class ApiMiddlewareTest(oz.testing.OzTestCase):
    forced_settings = {
        "allow_jsonp": True
    }

    def get_handlers(self):
        class UnknownErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise Exception("Test 1")

        class ApiErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise oz.plugins.json_api.ApiError("Test 2", code=401)

        class ResponseApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                self.respond({"hello": "world"})

        class BodyApiHandler(ApiMiddlewareTestHandler):
            def put(self):
                self.respond(self.body())

        return [
            ("/unknown_error_writer", UnknownErrorWritingApiHandler),
            ("/api_error_writer", ApiErrorWritingApiHandler),
            ("/response", ResponseApiHandler),
            ("/body", BodyApiHandler),
        ]

    def test_error_writer(self):
        self.http_client.fetch(self.get_url('/unknown_error_writer'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue("Exception: Test 1" in response.body)

        self.http_client.fetch(self.get_url('/api_error_writer'), self.stop)
        response = self.wait()
        json = tornado.escape.json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(json["code"], 401)
        self.assertEqual(json["error"], "Test 2")
        self.assertTrue("trace" in json)

    def test_respond(self):
        # Checks w/ JSONP support
        self.http_client.fetch(self.get_url('/response'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, '{"hello": "world"}')

        self.http_client.fetch(self.get_url('/response?callback=foo'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/javascript; charset=UTF-8")
        self.assertEqual(response.body, 'foo({"hello": "world"})')

        self.http_client.fetch(self.get_url('/response?callback=!!!'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue("Invalid callback identifier" in response.body)

    def test_body(self):
        # Invalid: no content-type specified
        self.http_client.fetch(self.get_url('/body'), self.stop, body='{"hello": "world"}', method="PUT")
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue("JSON body expected" in response.body, msg="Unexpected body: %s" % response.body)

        self.http_client.fetch(self.get_url('/body'), self.stop, body='{"hello": "world"}', method="PUT", headers={"Content-Type": "application/json"})
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, '{"hello": "world"}')

@oz.test
class NoJSONPApiMiddlewareTest(oz.testing.OzTestCase):
    forced_settings = {
        "allow_jsonp": False
    }

    def get_handlers(self):
        class NoJSONPResponseApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                self.respond({"hello": "world"})

        return [
            ("/nojsonp_response", NoJSONPResponseApiHandler),
        ]

    def test_respond(self):
        # Checks w/o JSONP support
        self.http_client.fetch(self.get_url('/nojsonp_response'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, '{"hello": "world"}')

        self.http_client.fetch(self.get_url('/nojsonp_response?callback=foo'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, '{"hello": "world"}')

        self.http_client.fetch(self.get_url('/nojsonp_response?callback=!!!'), self.stop)
        response = self.wait()
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, '{"hello": "world"}')

@oz.test
class NoDebugApiMiddlewareTest(oz.testing.OzTestCase):
    forced_settings = {
        "debug": False
    }

    def get_handlers(self):
        class NoDebugErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise oz.plugins.json_api.ApiError("Test 3", code=401)

        return [
            ("/nodebug_api_error_writer", NoDebugErrorWritingApiHandler),
        ]

    def test_error_writer(self):
        self.http_client.fetch(self.get_url('/nodebug_api_error_writer'), self.stop)
        response = self.wait()
        json = tornado.escape.json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(json["code"], 401)
        self.assertEqual(json["error"], "Test 3")
        self.assertTrue("trace" not in json)
