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
    mean_success_rate = float(sum([c.rewards for c in choices])) / max(sum([c.plays for c in choices]), 1)
    mean_failure_rate = 1 - mean_success_rate

    return sum([
        term(mean_success_rate * c.plays, c.rewards)
        + term(mean_failure_rate * c.plays, c.plays - c.rewards
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

        experiment = add_experiment(redis, new_experiment_name)

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
        old_choice_names = set(experiment.choice_names)

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
        self.redis = redis
        self.name = name
        self.refresh()

    def refresh(self):
        """Re-pulls the data from redis"""
        pipe = self.redis.pipeline()
        pipe.hget(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "metadata")
        pipe.hget(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "choices")
        pipe.hget(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "default-choice")
        results = pipe.execute()

        if results[0] == None:
            raise ExperimentException(self.name, "Does not exist")

        self.metadata = parse_json(results[0])
        self.choice_names = parse_json(results[1]) if results[1] != None else []
        self.default_choice = escape.to_unicode(results[2])
        self._choices = None

    @property
    def choices(self):
        """Gets the experiment choices"""

        if self._choices == None:
            self._choices = [ExperimentChoice(self, choice_name) for choice_name in self.choice_names]

        return self._choices

    def confidence(self):
        """
        Returns a tuple (chi squared, confident) of the experiment. Confident
        is simply a boolean specifying whether we're > 95%% sure that the
        results are statistically significant.
        """

        choices = self.choices

        # Get the chi-squared between the top two choices, if more than two choices exist
        if len(choices) >= 2:
            csq = chi_squared(*choices)
            confident = is_confident(csq, len(choices)) if len(choices) <= 10 else None
        else:
            csq = None
            confident = False

        return (csq, confident)

    def archive(self):
        """Archives an experiment"""
        pipe = self.redis.pipeline(transaction=True)
        pipe.srem(ACTIVE_EXPERIMENTS_REDIS_KEY, self.name)
        pipe.sadd(ARCHIVED_EXPERIMENTS_REDIS_KEY, self.name)
        pipe.execute()

    def add_choice(self, choice_name):
        """Adds a choice for the experiment"""

        if not ALLOWED_NAMES.match(choice_name):
            raise ExperimentException(self.name, "Illegal choice name: %s" % choice_name)

        if choice_name in self.choice_names:
            raise ExperimentException(self.name, "Choice already exists: %s" % choice_name)

        self.choice_names.append(choice_name)
        self.redis.hset(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "choices", escape.json_encode(self.choice_names))
        self.refresh()

    def remove_choice(self, choice_name):
        """Adds a choice for the experiment"""

        self.choice_names.remove(choice_name)
        self.redis.hset(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "choices", escape.json_encode(self.choice_names))
        self.refresh()

    def add_play(self, choice, count=1):
        """Increments the play count for a given experiment choice"""
        self.redis.hincrby(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "%s:plays" % choice, count)
        self._choices = None

    def add_reward(self, choice, count=1):
        """Increments the reward count for a given experiment choice"""
        self.redis.hincrby(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "%s:rewards" % choice, count)
        self._choices = None

    def compute_default_choice(self):
        """Computes and sets the default choice"""

        choices = self.choices

        if len(choices) == 0:
            return None

        high_choice = max(choices, key=lambda choice: choice.performance)
        self.redis.hset(EXPERIMENT_REDIS_KEY_TEMPLATE % self.name, "default-choice", high_choice.name)
        self.refresh()
        return high_choice

class ExperimentChoice(object):
    """Represents an experiment choice"""

    def __init__(self, experiment, name):
        self.experiment = experiment
        self.name = name
        self.refresh()

    def refresh(self):
        """Re-pulls the data from redis"""

        redis_key = EXPERIMENT_REDIS_KEY_TEMPLATE % self.experiment.name
        self.plays = int(self.experiment.redis.hget(redis_key, "%s:plays" % self.name) or 0)
        self.rewards = int(self.experiment.redis.hget(redis_key, "%s:rewards" % self.name) or 0)
        self.performance = float(self.rewards) / max(self.plays, 1)

def add_experiment(redis, name):
    """Adds a new experiment"""

    if not ALLOWED_NAMES.match(name):
        raise ExperimentException(name, "Illegal name")
    if redis.exists(EXPERIMENT_REDIS_KEY_TEMPLATE % name):
        raise ExperimentException(name, "Already exists")

    json = dict(creation_date=util.unicode_type(datetime.datetime.now()))
    pipe = redis.pipeline(transaction=True)
    pipe.sadd(ACTIVE_EXPERIMENTS_REDIS_KEY, name)
    pipe.hset(EXPERIMENT_REDIS_KEY_TEMPLATE % name, "metadata", escape.json_encode(json))
    pipe.execute()
    return Experiment(redis, name)

def get_experiments(redis, active=True):
    """Gets the full list of experiments"""

    key = ACTIVE_EXPERIMENTS_REDIS_KEY if active else ARCHIVED_EXPERIMENTS_REDIS_KEY
    return [Experiment(redis, escape.to_unicode(name)) for name in redis.smembers(key)]
