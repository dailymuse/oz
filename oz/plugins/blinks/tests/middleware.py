from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import oz.plugins.blinks

@oz.test
class BlinkMiddlewareTest(oz.testing.OzTestCase):
    def get_handlers(self):
        class BlinkHandler(oz.testing.FakeCookiesHandler, oz.plugins.blinks.BlinkMiddleware):
            def get(self):
                self.set_blink("Blink 1")
                self.set_blink("Blink #?", type="new_blink")
                self.finish("%s : %s" % self.get_blink())

        return [
            ("/", BlinkHandler),
        ]

    def test_blink(self):
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        self.assertEqual(response.body, "Blink #? : new_blink")
