from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.testing
import oz.bandit
from oz.redis_sessions import RedisSessionMiddleware
from oz.redis import RedisMiddleware
from tornado import web

@oz.test
class BanditMiddlewareTestCase(oz.testing.OzTestCase):
    forced_settings = {
        "session_salt": "abc"
    }

    def get_handlers(self):
        class ExperimentHandler(oz.testing.FakeCookiesHandler, RedisMiddleware, RedisSessionMiddleware, oz.bandit.BanditTestingMiddleware):
            def get(self, name):
                # Gets the choice for a given experiment
                choice = self.get_experiment_choice(name)

                if choice == None:
                    raise web.HTTPError(404)

                self.finish(choice)

            def post(self, name):
                # Sets a choice for a given experiment using the bandit algorithm
                exp = oz.bandit.add_experiment(self.redis(), name)
                exp.add_choice("A")
                exp.add_choice("B")
                exp.add_choice("C")

                self.choose_experiment(name)

            def put(self, name):
                # Explicitly sets a choice for a given experiment
                self.join_experiment(name, self.get_argument("choice"))

            def delete(self, name):
                # Removes the currently set choice for an experiment
                self.leave_experiment(name)

        return [
            (r"/experiment/(.+)", ExperimentHandler),
        ]

    def tearDown(self):
        super(oz.bandit.BanditMiddlewareTestCase, self).tearDown()
        
        # Clean up just in case there's keys still lying around
        redis = oz.redis.create_connection()

        for key in redis.keys("bandit:*:v2"):
            redis.delete(key)

    def test_get_experiment_choice(self):
        # Join a non-existent experiment
        response = self.request("/experiment/get-experiment-example?cookie_id=bandit")
        self.assertEqual(response.code, 404)

    def test_leave_experiment(self):
        # Leave a non-existent experiment
        response = self.request("/experiment/leave-experiment-example?cookie_id=bandit", method="DELETE")
        self.assertEqual(response.code, 200)

        # Create an experiment
        response = self.request("/experiment/leave-experiment-example?cookie_id=bandit", method="POST", body="")
        self.assertEqual(response.code, 200)

        # Leave the now existing experiment
        response = self.request("/experiment/leave-experiment-example?cookie_id=bandit", method="DELETE")
        self.assertEqual(response.code, 200)

    def test_choose_experiment(self):
        # Choose an experiment value
        response = self.request("/experiment/choose-experiment-example?cookie_id=bandit", method="POST", body="")
        self.assertEqual(response.code, 200)

        response = self.request("/experiment/choose-experiment-example?cookie_id=bandit")
        self.assertTrue(response.body in [b"A", b"B", b"C"])

    def test_join_experiment(self):
        # Create an experiment
        response = self.request("/experiment/join-experiment-example?cookie_id=bandit", method="POST", body="")
        self.assertEqual(response.code, 200)

        # Explicitly join an experiment choice
        response = self.request("/experiment/join-experiment-example?choice=B&cookie_id=bandit", method="PUT", body="")

        # Make sure we joined the right one
        response = self.request("/experiment/join-experiment-example?cookie_id=bandit")
        self.assertEqual(response.body, b"B")
