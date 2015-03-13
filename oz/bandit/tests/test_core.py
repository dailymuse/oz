from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz.bandit
import oz.redis
import unittest

class MockExperimentChoice(object):
    def __init__(self, plays, rewards):
        self.plays = plays
        self.rewards = rewards

class BanditCoreTestCase(unittest.TestCase):
    def tearDown(self):
        super(BanditCoreTestCase, self).tearDown()
        
        # Clean up just in case there's keys still lying around
        redis = oz.redis.create_connection()

        for key in redis.keys("bandit:*:v2"):
            redis.delete(key)

@oz.test
class IsConfidentTestCase(BanditCoreTestCase):
    """
    Tests chi squared and confidence calculations
    """

    def test_is_confident(self):
        self.assertFalse(oz.bandit.is_confident(3.83, 2))
        self.assertTrue(oz.bandit.is_confident(3.84, 2))
        self.assertFalse(oz.bandit.is_confident(5.98, 3))
        self.assertTrue(oz.bandit.is_confident(5.99, 3))

@oz.test
class ChiSquaredTestCase(BanditCoreTestCase):
    def test_chi_squared(self):
        # Make sure it returns 0 for an experiment with no results
        csq = oz.bandit.chi_squared(MockExperimentChoice(0, 0), MockExperimentChoice(0, 0))
        self.assertEqual(csq, 0)

        csq = oz.bandit.chi_squared(MockExperimentChoice(17, 3), MockExperimentChoice(19, 2))
        self.assertEqual(round(csq, 3), 0.380)

@oz.test
class SyncFromSpecTestCase(BanditCoreTestCase):
    def test_sync_from_spec(self):
        redis = oz.redis.create_connection()

        oz.bandit.sync_from_spec(redis, {
            "ex-sync-1": ["a", "b", "c"],
            "ex-sync-2": ["d", "e", "f"],
            "ex-sync-3": ["g", "h", "i"],
        })

        # Check that the experiments/choices were made
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-1").choice_names, ["a", "b", "c"])
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-2").choice_names, ["d", "e", "f"])
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-3").choice_names, ["g", "h", "i"])

        # Should delete ex-sync-1, preserve ex-sync-2, modify ex-sync-3, and
        # create an ex-sync-4
        oz.bandit.sync_from_spec(redis, {
            "ex-sync-2": ["d", "e", "f"],
            "ex-sync-3": ["g", "h", "j", "k"],
            "ex-sync-4": ["l", "m", "n"],
        })

        # Check that ex-sync-1 is archived
        archived_experiment_names = set([experiment.name for experiment in oz.bandit.get_experiments(redis, active=False)])
        self.assertTrue("ex-sync-1" in archived_experiment_names)

        # Check that ex-sync-1 choices were not changed
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-1").choice_names, ["a", "b", "c"])

        # Check that ex-sync-2 has the same choices
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-2").choice_names, ["d", "e", "f"])

        # Check that ex-sync-3 has the modified choices
        # Compares sets since the choices could be arbitrarily reordered
        self.assertEqual(set(oz.bandit.Experiment(redis, "ex-sync-3").choice_names), set(["g", "h", "j", "k"]))

        # Check that ex-sync-4 has been setup
        self.assertEqual(oz.bandit.Experiment(redis, "ex-sync-4").choice_names, ["l", "m", "n"])

@oz.test
class AddExperimentTestCase(BanditCoreTestCase):
    def test_add_experiment(self):
        redis = oz.redis.create_connection()

        self.assertRaises(oz.bandit.ExperimentException, oz.bandit.add_experiment, redis, "illegal name")

        experiment = oz.bandit.add_experiment(redis, "ex-add-experiment")
        self.assertEqual(experiment.name, "ex-add-experiment")

@oz.test
class GetExperimentsTestCase(BanditCoreTestCase):
    def test_get_experiments(self):
        redis = oz.redis.create_connection()

        self.assertEqual(len(oz.bandit.get_experiments(redis, active=True)), 0)
        self.assertEqual(len(oz.bandit.get_experiments(redis, active=False)), 0)

        active_experiment = oz.bandit.add_experiment(redis, "ex-get-experiments-1")
        inactive_experiment = oz.bandit.add_experiment(redis, "ex-get-experiments-2")
        inactive_experiment.archive()

        active_experiments = oz.bandit.get_experiments(redis, active=True)
        self.assertEqual(len(active_experiments), 1)
        self.assertEqual(active_experiments[0].name, active_experiment.name)

        inactive_experiments = oz.bandit.get_experiments(redis, active=False)
        self.assertEqual(len(inactive_experiments), 1)
        self.assertEqual(inactive_experiments[0].name, inactive_experiment.name)

@oz.test
class ExperimentTestCase(BanditCoreTestCase):
    def test_metadata(self):
        redis = oz.redis.create_connection()
        experiment = oz.bandit.add_experiment(redis, "ex-metadata")
        self.assertNotEqual(experiment.metadata, None)

    def test_choice_names(self):
        redis = oz.redis.create_connection()
        experiment = oz.bandit.add_experiment(redis, "ex-choice-names")

        self.assertRaises(oz.bandit.ExperimentException, experiment.add_choice, "illegal name")
        self.assertEqual(experiment.choice_names, [])

        experiment.add_choice("A")
        experiment.add_choice("B")
        self.assertEqual(experiment.choice_names, ["A", "B"])

        experiment.remove_choice("B")
        self.assertEqual(experiment.choice_names, ["A"])

    def test_default_choice(self):
        redis = oz.redis.create_connection()
        experiment = oz.bandit.add_experiment(redis, "ex-default-choice")
        experiment.add_choice("A")
        experiment.add_choice("B")
        self.assertEqual(experiment.default_choice, None)

        # Should simply set it to the first choice (A) since there's no data
        experiment.compute_default_choice()
        self.assertEqual(experiment.default_choice, "A")

        # Should keep it at A
        experiment.add_play("B")
        experiment.compute_default_choice()
        self.assertEqual(experiment.default_choice, "A")

        # Should set it to B
        experiment.add_reward("B")
        experiment.compute_default_choice()
        self.assertEqual(experiment.default_choice, "B")

    def test_confidence(self):
        redis = oz.redis.create_connection()

        experiment = oz.bandit.add_experiment(redis, "ex-confidence")
        experiment.add_choice("arm1")
        experiment.add_choice("arm2")

        # Add data to the experiment
        experiment.add_play("arm1", count=17)
        experiment.add_reward("arm1", count=3)
        experiment.add_play("arm2", count=19)
        experiment.add_reward("arm2", count=2)

        csq, confident = experiment.confidence()
        self.assertEqual(round(csq, 3), 0.380)
        self.assertFalse(confident)

    def test_add_play(self):
        redis = oz.redis.create_connection()

        experiment = oz.bandit.add_experiment(redis, "ex-plays")
        experiment.add_choice("foo")

        self.assertEqual(experiment.choices[0].plays, 0)
        experiment.add_play("foo")
        self.assertEqual(experiment.choices[0].plays, 1)

    def test_add_reward(self):
        redis = oz.redis.create_connection()

        experiment = oz.bandit.add_experiment(redis, "ex-rewards")
        experiment.add_choice("foo")

        self.assertEqual(experiment.choices[0].rewards, 0)
        experiment.add_reward("foo")
        self.assertEqual(experiment.choices[0].rewards, 1)
