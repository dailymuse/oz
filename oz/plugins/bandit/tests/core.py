from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz.plugins.bandit
import oz.plugins.redis
import unittest

@oz.test
class ChiSquaredTest(unittest.TestCase):
    def test_get_chi_squared(self):

        # Make sure it returns 0 for an experiment with no results
        csq = oz.plugins.bandit.get_chi_squared(0, 0, 0, 0)
        self.assertEqual(csq, 0)

        csq = oz.plugins.bandit.get_chi_squared(17, 3, 19, 2)
        self.assertEqual(round(csq, 3), 0.328)

@oz.test
class BanditCoreTest(unittest.TestCase):
    def tearDown(self):
        super(BanditCoreTest, self).tearDown()
        
        # Clean up just in case there's keys still lying around
        redis = oz.plugins.redis.create_connection()

        for key in redis.keys("bandit:*:v2"):
            redis.delete(key)

    def test_exists(self):
        redis = oz.plugins.redis.create_connection()
        experiment = oz.plugins.bandit.Experiment(redis, "ex-exists")
        self.assertFalse(experiment.exists())
        experiment.add()
        self.assertTrue(experiment.exists())

    def test_archive(self):
        redis = oz.plugins.redis.create_connection()
        experiment = oz.plugins.bandit.Experiment(redis, "ex-archived")

        self.assertEqual(redis.scard(oz.plugins.bandit.ACTIVE_EXPERIMENTS_REDIS_KEY), 0)
        self.assertEqual(redis.scard(oz.plugins.bandit.ARCHIVED_EXPERIMENTS_REDIS_KEY), 0)

        experiment.add()
        self.assertEqual(redis.scard(oz.plugins.bandit.ACTIVE_EXPERIMENTS_REDIS_KEY), 1)
        self.assertEqual(redis.scard(oz.plugins.bandit.ARCHIVED_EXPERIMENTS_REDIS_KEY), 0)

        experiment.archive()
        self.assertEqual(redis.scard(oz.plugins.bandit.ACTIVE_EXPERIMENTS_REDIS_KEY), 0)
        self.assertEqual(redis.scard(oz.plugins.bandit.ARCHIVED_EXPERIMENTS_REDIS_KEY), 1)

    def test_metadata(self):
        redis = oz.plugins.redis.create_connection()
        experiment = oz.plugins.bandit.Experiment(redis, "ex-metadata")
        self.assertEqual(experiment.metadata(), None)
        experiment.add()
        self.assertNotEqual(experiment.metadata(), None)

    def test_choices(self):
        redis = oz.plugins.redis.create_connection()
        experiment = oz.plugins.bandit.Experiment(redis, "ex-choices")

        self.assertRaises(lambda: experiment.add_choice("illegal name"))
        self.assertEqual(experiment.choices(), [])

        experiment.add_choice("A")
        experiment.add_choice("B")
        self.assertEqual(experiment.choices(), ["A", "B"])

        experiment.remove_choice("B")
        self.assertEqual(experiment.choices(), ["A"])

    def test_plays(self):
        redis = oz.plugins.redis.create_connection()

        experiment = oz.plugins.bandit.Experiment(redis, "ex-plays")
        experiment.add()

        # Make sure there are no plays
        self.assertEqual(experiment.plays("foo"), 0)

        # Add a play
        experiment.add_play("foo")

        # Make sure the play exists
        self.assertEqual(experiment.plays("foo"), 1)

    def test_rewards(self):
        redis = oz.plugins.redis.create_connection()

        experiment = oz.plugins.bandit.Experiment(redis, "ex-rewards")
        experiment.add()

        # Make sure there are no rewards
        self.assertEqual(experiment.rewards("foo"), 0)

        # Add a reward
        experiment.add_reward("foo")

        # Make sure the reward exists
        self.assertEqual(experiment.rewards("foo"), 1)

    def test_default_choice(self):
        redis = oz.plugins.redis.create_connection()

        experiment = oz.plugins.bandit.Experiment(redis, "ex-default-choice")
        experiment.add()

        self.assertEqual(experiment.get_default_choice(), None)
        experiment.set_default_choice("asd")
        self.assertEqual(experiment.get_default_choice(), "asd")

    def test_results(self):
        redis = oz.plugins.redis.create_connection()

        experiment = oz.plugins.bandit.Experiment(redis, "ex-data")
        experiment.add()

        experiment.add_choice("arm1")
        experiment.add_choice("arm2")

        # Add data to the experiment
        experiment.add_play("arm1", count=17)
        experiment.add_reward("arm1", count=3)
        experiment.add_play("arm2", count=19)
        experiment.add_reward("arm2", count=2)

        data = experiment.results()

        self.assertEqual(data["name"], "ex-data")
        self.assertNotEqual(data["metadata"], None)
        self.assertEqual(data["default"], "arm1")
        self.assertEqual(round(data["chi_squared"], 3), 0.328)

        self.assertEqual(len(data["choices"]), 2)

        arm1 = data["choices"][0]
        self.assertEqual(arm1["name"], "arm1")
        self.assertEqual(round(arm1["results"], 3), 0.176)
        self.assertEqual(arm1["plays"], 17)
        self.assertEqual(arm1["rewards"], 3)

        arm2 = data["choices"][1]
        self.assertEqual(arm2["name"], "arm2")
        self.assertEqual(round(arm2["results"], 3), 0.105)
        self.assertEqual(arm2["plays"], 19)
        self.assertEqual(arm2["rewards"], 2)
