from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from tornado import escape
from .actions import *
from .middleware import *
from .tests import *
import re

ACTIVE_EXPERIMENTS_REDIS_KEY = "bandit:listing:active:v2"
ARCHIVED_EXPERIMENTS_REDIS_KEY = "bandit:listing:archived:v2"
EXPERIMENT_REDIS_KEY_TEMPLATE = "bandit:experiment:%s:v2"
ALLOWED_NAMES = re.compile("^[A-Za-z0-9-_]+$")

def get_chi_squared(choice1_plays, choice1_rewards, choice2_plays, choice2_rewards):
    """Calculates chi-squared between two choices"""

    # Currently not set up to calculate chi_squared for more than 2 arms
    exp_0 = (float(choice1_rewards) + choice2_rewards) / ((choice1_plays + choice2_plays) or 1) * choice1_plays
    exp_1 = (float(choice1_rewards) + choice2_rewards) / ((choice1_plays + choice2_plays) or 1) * choice2_plays

    if exp_0 > 0 and exp_1 > 0:
        return (exp_0 - float(choice1_rewards)) ** 2 / exp_0 + (exp_1 - float(choice2_rewards)) ** 2 / exp_1
    else:
        return 0

class ExperimentException(Exception):
    """
    An exception for issues related to experiments. This way applications can
    catch the exception and respond accordingly.
    """

    def __init__(self, experiment_name, message):
        super(ExperimentException, self).__init__("Experiment %s: %s" % (experiment_name, message))
        self.experiment_name = experiment_name

class Experiment(object):
    def __init__(self, redis, name):
        if not ALLOWED_NAMES.match(name):
            raise ExperimentException(name, "Illegal name")

        self.redis = redis
        self.name = name

    def _redis_key(self):
        return EXPERIMENT_REDIS_KEY_TEMPLATE % self.name

    def exists(self):
        """Checks whether this experiment exists"""
        return self.redis.exists(self._redis_key())

    def add(self):
        """Adds the new experiment"""

        # Check to ensure the experiment doesn't already exists
        if self.exists():
            raise ExperimentException(self.name, "already exists")

        # Add the experiment
        json = dict(creation_date=unicode(datetime.datetime.now()))
        pipe = self.redis.pipeline(transaction=True)
        pipe.sadd(ACTIVE_EXPERIMENTS_REDIS_KEY, self.name)
        pipe.hset(self._redis_key(), "metadata", escape.json_encode(json))
        pipe.execute()

    def archive(self):
        """Archives an experiment"""

        if not self.exists():
            raise ExperimentException(self.name, "does not exist") 

        pipe = self.redis.pipeline(transaction=True)
        pipe.srem(ACTIVE_EXPERIMENTS_REDIS_KEY, self.name)
        pipe.sadd(ARCHIVED_EXPERIMENTS_REDIS_KEY, self.name)
        pipe.execute()

    def metadata(self):
        """Gets the properties associated with this experiment"""
        raw = self.redis.hget(self._redis_key(), "metadata")
        return escape.json_decode(raw) if raw != None else None

    def choices(self):
        """Gets the choices available"""
        choices = self.redis.hget(self._redis_key(), "choices")
        return escape.json_decode(choices) if choices != None else []

    def add_choice(self, choice):
        """Adds a choice for the experiment"""

        if not ALLOWED_NAMES.match(choice):
            raise ExperimentException(self.name, "Illegal choice name: %s" % choice)

        choices = self.choices()
        choices.append(choice)
        self.redis.hset(self._redis_key(), "choices", escape.json_encode(choices))

    def remove_choice(self, choice):
        """Adds a choice for the experiment"""

        if not ALLOWED_NAMES.match(choice):
            raise ExperimentException(self.name, "Illegal choice name: %s" % choice)

        choices = self.choices()
        choices.remove(choice)
        self.redis.hset(self._redis_key(), "choices", escape.json_encode(choices))

    def plays(self, choice):
        """Gets the play count associated with an experiment choice"""
        return int(self.redis.hget(self._redis_key(), "%s:plays" % choice) or 0)

    def add_play(self, choice, count=1):
        """Increments the play count for a given experiment choice"""
        self.redis.hincrby(self._redis_key(), "%s:plays" % choice, count)

    def rewards(self, choice):
        """Gets the reward count associated with an experiment choice"""
        return int(self.redis.hget(self._redis_key(), "%s:rewards" % choice) or 0)

    def add_reward(self, choice, count=1):
        """Increments the reward count for a given experiment choice"""
        self.redis.hincrby(self._redis_key(), "%s:rewards" % choice, count)

    def get_default_choice(self):
        """Gets the default choice for this experiment"""
        return self.redis.hget(self._redis_key(), "default-choice")

    def set_default_choice(self, choice):
        """Sets the default choice for this experiment"""
        self.redis.hset(self._redis_key(), "default-choice", choice)

    def results(self):
        """
        Gets all of the data associated with this experiment, and stores it in
        a JSON-serializable data structure
        """

        if not self.exists():
            raise ExperimentException(self.name, "does not exist")

        # Build a list of all the choices
        choices = []

        for choice in self.choices():
            plays = self.plays(choice)
            rewards = self.rewards(choice)
            results = rewards / (plays or 1)
            choices.append(dict(name=choice, plays=plays, rewards=rewards, results=results))

        # Find the top two choices
        choices.sort(key=lambda c: c["results"], reverse=True)

        # Set the default choice for this experiment
        if len(choices) >= 1:
            self.set_default_choice(choices[0]["name"])

        # Get the chi-squared between the top two choices, if more than two choices exist
        if len(choices) >= 2:
            chi_squared = get_chi_squared(choices[0]["plays"], choices[0]["rewards"], choices[1]["plays"], choices[1]["rewards"])
        else:
            chi_squared = None
        
        # Return the results
        return {
            "name": self.name,
            "metadata": self.metadata(),
            "default": self.get_default_choice(),
            "chi_squared": chi_squared,
            "choices": choices
        }

def get_experiments(redis, active=True):
    """Gets the full list of experiments"""

    key = ACTIVE_EXPERIMENTS_REDIS_KEY if active else ARCHIVED_EXPERIMENTS_REDIS_KEY
    return [Experiment(redis, name) for name in redis.smembers(key)]
