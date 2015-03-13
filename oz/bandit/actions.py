from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import datetime
import oz.redis
import oz.bandit
from tornado import escape

@oz.action
def add_experiment(experiment):
    """Adds a new experiment"""
    redis = oz.redis.create_connection()
    oz.bandit.add_experiment(redis, experiment)

@oz.action
def archive_experiment(experiment):
    """Archives an experiment"""
    redis = oz.redis.create_connection()
    oz.bandit.Experiment(redis, experiment).archive()

@oz.action
def add_experiment_choice(experiment, choice):
    """Adds an experiment choice"""
    redis = oz.redis.create_connection()
    oz.bandit.Experiment(redis, experiment).add_choice(choice)

@oz.action
def remove_experiment_choice(experiment, choice):
    """Removes an experiment choice"""
    redis = oz.redis.create_connection()
    oz.bandit.Experiment(redis, experiment).remove_choice(choice)

@oz.action
def get_experiment_results():
    """
    Computes the results of all experiments, stores it in redis, and prints it
    out
    """

    redis = oz.redis.create_connection()

    for experiment in oz.bandit.get_experiments(redis):
        experiment.compute_default_choice()
        csq, confident = experiment.confidence()

        print("%s:" % experiment.name)
        print("- creation date: %s" % experiment.metadata["creation_date"])
        print("- default choice: %s" % experiment.default_choice)
        print("- chi squared: %s" % csq)
        print("- confident: %s" % confident)
        print("- choices:")

        for choice in experiment.choices:
            print("  - %s: plays=%s, rewards=%s, performance=%s" % (choice.name, choice.plays, choice.rewards, choice.performance))

@oz.action
def sync_experiments_from_spec(filename):
    """
    Takes the path to a JSON file declaring experiment specifications, and
    modifies the experiments stored in redis to match the spec.

    A spec looks like this:
    {
       "experiment 1": ["choice 1", "choice 2", "choice 3"],
       "experiment 2": ["choice 1", "choice 2"]
    }
    """

    redis = oz.redis.create_connection()

    with open(filename, "r") as f:
        schema = escape.json_decode(f.read())

    oz.bandit.sync_from_spec(redis, schema)
