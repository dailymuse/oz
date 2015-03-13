"""Middleware for the bandit plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import random
import oz.bandit
from tornado import escape

class BanditTestingMiddleware(object):
    def __init__(self):
        super(BanditTestingMiddleware, self).__init__()
        self.template_helper("get_experiment_choice", self.get_experiment_choice)
        self.template_helper("choose_experiment", self.choose_experiment)

    def session_key(self, experiment):
        """Gets the session key for an experiment"""
        return "bandit:%s:v1" % experiment

    def join_experiment(self, experiment, choice):
        """Opts the current user into an experiment choice"""
        self.set_session_value(self.session_key(experiment), choice)

    def leave_experiment(self, experiment):
        """Boots the current user out of an experiment"""
        self.clear_session_value(self.session_key(experiment))

    def get_experiment_choice(self, experiment):
        """Gets the experiment choice a user is in"""
        return escape.to_unicode(self.get_session_value(self.session_key(experiment)))

    def choose_experiment(self, name):
        """
        Opts a user into one of many choices for an experiment. They have a
        90 percent chance of being opted into the default choice (the one with
        the greatest results.) Otherwise they join a random choice (including
        potentially the default choice anyway.)
        """

        experiment = oz.bandit.Experiment(self.redis(), name)
        choice = self.get_experiment_choice(name)

        # If the currently selected user choice is no longer valid, nullify it
        if not choice in experiment.choice_names:
            choice = None

        if not choice:
            if random.random() >= 0.1:
                # Join the best performing choice
                default_choice = experiment.default_choice

                if default_choice:
                    choice = default_choice

            if not choice and len(experiment.choice_names) > 0:
                # Join a random choice
                choice = random.choice(experiment.choice_names)

            # Opt the user in
            if choice:
                self.join_experiment(name, choice)

        # Add to the play count for the selected choice
        if choice:
            experiment.add_play(choice)

        return choice

    def experiment_success(self, name):
        """
        Marks the user's current choice as successful - i.e. the user
        converted, or clicked-through, etc.
        """
        choice = self.get_experiment_choice(name)
        experiment = oz.bandit.Experiment(self.redis(), name)
        experiment.add_reward(choice)
