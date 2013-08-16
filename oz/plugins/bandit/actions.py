from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import datetime

import oz.plugins.redis
import oz.plugins.bandit

@oz.action
def add_experiment(experiment):
    """Adds a new experiment"""
    redis = oz.plugins.redis.create_connection()
    oz.plugins.bandit.Experiment(redis, experiment).add()

@oz.action
def archive_experiment(experiment):
    """Archives an experiment"""
    redis = oz.plugins.redis.create_connection()
    oz.plugins.bandit.Experiment(redis, experiment).archive()

@oz.action
def add_experiment_choice(experiment, choice):
    """Adds an experiment choice"""
    redis = oz.plugins.redis.create_connection()
    oz.plugins.bandit.Experiment(redis, experiment).add_choice(choice)

@oz.action
def remove_experiment_choice(experiment, choice):
    """Removes an experiment choice"""
    redis = oz.plugins.redis.create_connection()
    oz.plugins.bandit.Experiment(redis, experiment).remove_choice(choice)

@oz.action
def get_experiment_results():
    """
    Computes the results of all experiments, stores it in redis, and prints it
    out
    """

    redis = oz.plugins.redis.create_connection()

    for experiment in oz.plugins.bandit.get_experiments(redis):
        data = experiment.results()

        print("%s:" % data["name"])
        print("- creation date: %s" % data["metadata"]["creation_date"])
        print("- default choice: %s" % data["default"])
        print("- chi squared: %s" % data["chi_squared"])
        print("- choices:")

        for choice_data in data["choices"]:
            print("  - %s: plays=%s, rewards=%s, result=%s" % (choice_data["name"], choice_data["plays"], choice_data["rewards"], choice_data["results"]))
