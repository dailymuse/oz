from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import oz.blinks

@oz.test
class BlinkMiddlewareTestCase(oz.testing.OzTestCase):
    def get_handlers(self):
        class BlinkHandler(oz.testing.FakeCookiesHandler, oz.blinks.BlinkMiddleware):
            def get(self):
                self.finish("%s:%s" % self.get_blink())

            def put(self):
                self.set_blink(self.get_argument("value"), type=self.get_argument("type"))

        return [
            ("/", BlinkHandler),
        ]

    def test_blink(self):
        response = self.request("/?cookie_id=blinks")
        self.assertEqual(response.body, b"None:None")

        response = self.request("/?value=A&type=B&cookie_id=blinks", method="PUT", body="")
        self.assertEqual(response.code, 200)

        response = self.request("/?cookie_id=blinks")
        self.assertEqual(response.body, b"A:B")
