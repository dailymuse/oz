from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import oz.plugins.bandit
from oz.plugins.bandit import BanditTestingMiddleware
from oz.plugins.redis_sessions import RedisSessionMiddleware
from oz.plugins.redis import RedisMiddleware

@oz.test
class BanditMiddlewareTest(oz.testing.OzTestCase):
    forced_settings = {
        "session_salt": "abc"
    }

    def get_handlers(self):
        class BanditHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware, BanditTestingMiddleware):
            def post(self):
                choice = self.choose_experiment("ex-middleware")
                self.finish(choice)

            def get(self):
                self.experiment_success("ex-middleware")
                choice = self.get_experiment_choice("ex-middleware")
                redis = self.redis()
                experiment = oz.plugins.bandit.Experiment(redis, "ex-middleware")
                self.finish("%s:%s" % (experiment.plays(choice), experiment.rewards(choice)))

        return [
            ("/bandit", BanditHandler),
        ]

    def tearDown(self):
        super(BanditMiddlewareTest, self).tearDown()
        
        # Clean up just in case there's keys still lying around
        redis = oz.plugins.redis.create_connection()

        for key in redis.keys("bandit:*:v2"):
            redis.delete(key)

    def test_bandit(self):
        redis = oz.plugins.redis.create_connection()

        experiment = oz.plugins.bandit.Experiment(redis, "ex-middleware")
        experiment.add()

        for choice in ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]:
            experiment.add_choice(choice)

        # Add an empty-ish body because tornado's simple_httpclient requires it
        self.http_client.fetch(self.get_url("/bandit?cookie_id=test_bandit"), self.stop, method="POST", body=" ")
        response = self.wait()
        choice = response.body
        self.assertIn(choice, ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"])

        self.http_client.fetch(self.get_url("/bandit?cookie_id=test_bandit"), self.stop, method="POST", body=" ")
        response = self.wait()
        self.assertEqual(response.body, choice)

        self.http_client.fetch(self.get_url("/bandit?cookie_id=test_bandit"), self.stop)
        response = self.wait()
        self.assertEqual(response.body, "2:1")
