from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing

from oz.json_api import ApiMiddleware, ApiError
import tornado.escape

class ApiMiddlewareTestHandler(oz.RequestHandler, ApiMiddleware):
    def initialize(self, *args, **kwargs):
        super(ApiMiddlewareTestHandler, self).initialize(*args, **kwargs)

@oz.test
class ApiMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "allow_jsonp": True
    }

    def get_handlers(self):
        class UnknownErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise Exception("Test 1")

        class ApiErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise ApiError("Test 2", code=401)

        class ResponseApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                self.respond({"hello": "world"})

        class BodyApiHandler(ApiMiddlewareTestHandler):
            def put(self):
                self.respond(self.body())

        return [
            ("/unknown-error", UnknownErrorWritingApiHandler),
            ("/api-error", ApiErrorWritingApiHandler),
            ("/response", ResponseApiHandler),
            ("/body", BodyApiHandler),
        ]

    def test_error_writer(self):
        response = self.request("/unknown-error")
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue(b"Exception: Test 1" in response.body)

        response = self.request("/api-error")
        json = tornado.escape.json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(json["code"], 401)
        self.assertEqual(json["error"], "Test 2")
        self.assertTrue("trace" in json)

    def test_respond(self):
        # Checks w/ JSONP support
        response = self.request("/response")
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, b'{"hello": "world"}')

        response = self.request("/response?callback=foo")
        self.assertEqual(response.headers["Content-Type"], "application/javascript; charset=UTF-8")
        self.assertEqual(response.body, b'foo({"hello": "world"})')

        response = self.request('/response?callback=!!!')
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue(b"Invalid callback identifier" in response.body)

    def test_body(self):
        # Invalid: no content-type specified
        response = self.request('/body', body='{"hello": "world"}', method="PUT")
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertTrue(b"JSON body expected" in response.body, msg="Unexpected body: %s" % response.body)

        response = self.request('/body', body='{"hello": "world"}', method="PUT", headers={"Content-Type": "application/json"})
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, b'{"hello": "world"}')

@oz.test
class NoJSONPApiMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "allow_jsonp": False
    }

    def get_handlers(self):
        class NoJSONPResponseApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                self.respond({"hello": "world"})

        return [
            ("/nojsonp-response", NoJSONPResponseApiHandler),
        ]

    def test_respond(self):
        # Checks w/o JSONP support
        response = self.request('/nojsonp-response')
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, b'{"hello": "world"}')

        response = self.request('/nojsonp-response?callback=foo')
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, b'{"hello": "world"}')

        response = self.request('/nojsonp-response?callback=!!!')
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(response.body, b'{"hello": "world"}')

@oz.test
class NoDebugApiMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "debug": False
    }

    def get_handlers(self):
        class NoDebugErrorWritingApiHandler(ApiMiddlewareTestHandler):
            def get(self):
                raise ApiError("Test 3", code=401)

        return [
            ("/nodebug-api-error", NoDebugErrorWritingApiHandler),
        ]

    def test_error_writer(self):
        response = self.request('/nodebug-api-error')
        json = tornado.escape.json_decode(response.body)
        self.assertEqual(response.code, 401)
        self.assertEqual(response.headers["Content-Type"], "application/json; charset=UTF-8")
        self.assertEqual(json["code"], 401)
        self.assertEqual(json["error"], "Test 3")
        self.assertTrue("trace" not in json)
