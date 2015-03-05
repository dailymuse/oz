"""Bandit testing plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from tornado import escape, util
from .actions import *
from .middleware import *
from .tests import *
import re

ACTIVE_EXPERIMENTS_REDIS_KEY = "bandit:listing:active:v2"
ARCHIVED_EXPERIMENTS_REDIS_KEY = "bandit:listing:archived:v2"
EXPERIMENT_REDIS_KEY_TEMPLATE = "bandit:experiment:%s:v2"
ALLOWED_NAMES = re.compile("^[A-Za-z0-9-_]+$")

# Via http://passel.unl.edu/Image/Namuth-CovertDeana956176274/chi-sqaure%20distribution%20table.PNG
# Ideally this would be computed on-the-fly. If you know your differential
# equations, PR please!
CHI_SQUARE_DISTRIBUTION = [
    3.84,
    5.99,
    7.81,
    9.49,
    11.07,
    12.59,
    14.07,
    15.51,
    16.92,
    18.31,
    19.68,
    21.03,
    22.36,
    23.68,
    25.00,
    26.30,
    27.59,
    28.87,
    30.14,
    31.41,
]

def chi_squared(*choices):
    """Calculates the chi squared"""

    term = lambda expected, observed: float((expected - observed) ** 2) / max(expected, 1)
    mean_success_rate = float(sum([c["rewards"] for c in choices])) / max(sum([c["plays"] for c in choices]), 1)
    mean_failure_rate = 1 - mean_success_rate

    return sum([
        term(mean_success_rate * c["plays"], c["rewards"])
        + term(mean_failure_rate * c["plays"], c["plays"] - c["rewards"]
    ) for c in choices])

def is_confident(csq, num_choices):
    """
    Returns whether an experiment is statistically significant with 95%%
    confidence
    """
    return csq >= CHI_SQUARE_DISTRIBUTION[num_choices - 2]

def parse_json(raw):
    """Parses raw bytes to a JSON object with unicode strings"""
    return escape.recursive_unicode(escape.json_decode(raw)) if raw != None else None

def sync_from_spec(redis, schema):
    """
    Takes an input experiment spec and creates/modifies/archives the existing
    experiments to match the spec.

    If there's an experiment in the spec that currently doesn't exist, it will
    be created along with the associated choices.

    If there's an experiment in the spec that currently exists, and the set of
    choices are different, that experiment's choices will be modified to match
    the spec.

    If there's an experiment not in the spec that currently exists, it will be
    archived.

    A spec looks like this:

    {
       "experiment 1": ["choice 1", "choice 2", "choice 3"],
       "experiment 2": ["choice 1", "choice 2"]
    }
    """

    def get_experiments_dict(active=True):
        """Returns a dictionary of experiment names -> experiment objects"""
        return dict((experiment.name, experiment) for experiment in get_experiments(redis, active=active))

    # Get the current experiments
    active_experiments = get_experiments_dict()
    archived_experiments = get_experiments_dict(active=False)

    # Get the newly defined experiment names and the names of the experiments
    # already setup
    new_experiment_names = set(schema.keys())
    active_experiment_names = set(active_experiments.keys())

    # Find all the experiments that are in the schema and are defined among the
    # archived experiments, but not the active ones (we check against active
    # experiments to prevent the edge case where an experiment might be defined
    # doubly in both active and archived experiments)
    unarchivable_experiment_names = (new_experiment_names - active_experiment_names) & set(archived_experiments.keys())

    # De-archive the necessary experiments
    for unarchivable_experiment_name in unarchivable_experiment_names:
        print("- De-archiving %s" % unarchivable_experiment_name)

        # Because there is no function to de-archive an experiment, it must
        # be done manually
        pipe = redis.pipeline(transaction=True)
        pipe.sadd(ACTIVE_EXPERIMENTS_REDIS_KEY, unarchivable_experiment_name)
        pipe.srem(ARCHIVED_EXPERIMENTS_REDIS_KEY, unarchivable_experiment_name)
        pipe.execute()

    # Reload the active experiments if we de-archived any
    if unarchivable_experiment_names:
        active_experiments = get_experiments_dict()
        active_experiment_names = set(active_experiments.keys())

    # Create the new experiments
    for new_experiment_name in new_experiment_names - active_experiment_names:
        print("- Creating experiment %s" % new_experiment_name)

        experiment = Experiment(redis, new_experiment_name)
        experiment.add()

        for choice in schema[new_experiment_name]:
            print("  - Adding choice %s" % choice)
            experiment.add_choice(choice)

    # Archive experiments not defined in the schema
    for archivable_experiment_name in active_experiment_names - new_experiment_names:
        print("- Archiving %s" % archivable_experiment_name)
        active_experiments[archivable_experiment_name].archive()

    # Update the choices for existing experiments that are also defined in the
    # schema
    for experiment_name in new_experiment_names & active_experiment_names:
        experiment = active_experiments[experiment_name]
        new_choice_names = set(schema[experiment_name])
        old_choice_names = set(experiment.choices())

        # Add choices in the schema that do not exist yet
        for new_choice_name in new_choice_names - old_choice_names:
            print("- Adding choice %s to existing experiment %s" % (new_choice_name, experiment_name))
            experiment.add_choice(new_choice_name)

        # Remove choices that aren't in the schema
        for removable_choice_name in old_choice_names - new_choice_names:
            print("- Removing choice %s from existing experiment %s" % (removable_choice_name, experiment_name))
            experiment.remove_choice(removable_choice_name)

class ExperimentException(Exception):
    """
    An exception for issues related to experiments. This way applications can
    catch the exception and respond accordingly.
    """

    def __init__(self, experiment_name, message):
        super(ExperimentException, self).__init__("Experiment %s: %s" % (experiment_name, message))
        self.experiment_name = experiment_name

class Experiment(object):
    """Specification for a bandit experiment"""

    def __init__(self, redis, name):
        if not ALLOWED_NAMES.match(name):
            raise ExperimentException(name, "Illegal name")

        self.redis = redis
        self.name = name

    def _redis_key(self):
        """Gets the redis key for this experiment"""
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
        json = dict(creation_date=util.unicode_type(datetime.datetime.now()))
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
        return parse_json(self.redis.hget(self._redis_key(), "metadata"))

    def choices(self):
        """Gets the choices available"""
        return parse_json(self.redis.hget(self._redis_key(), "choices")) or []

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
        return escape.to_unicode(self.redis.hget(self._redis_key(), "default-choice"))

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
            csq = chi_squared(*choices)
            confident = is_confident(csq, len(choices)) if len(choices) <= 10 else None
        else:
            csq = None
            confident = False
        
        # Return the results
        return {
            "name": self.name,
            "metadata": self.metadata(),
            "default": self.get_default_choice(),
            "chi_squared": csq,
            "confident": confident,
            "choices": choices
        }

def get_experiments(redis, active=True):
    """Gets the full list of experiments"""

    key = ACTIVE_EXPERIMENTS_REDIS_KEY if active else ARCHIVED_EXPERIMENTS_REDIS_KEY
    return [Experiment(redis, name) for name in redis.smembers(key)]
