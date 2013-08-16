from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import random
import oz.plugins.bandit

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
        return self.get_session_value(self.session_key(experiment))

    def choose_experiment(self, name):
        """
        Opts a user into one of many choices for an experiment. They have a
        90 percent chance of being opted into the default choice (the one with
        the greatest results.) Otherwise they join a random choice (including
        potentially the default choice anyway.)
        """

        redis = self.redis()
        experiment = oz.plugins.bandit.Experiment(redis, name)
        experiment_choices = experiment.choices()
        choice = self.get_experiment_choice(name)

        # If the currently selected user choice is no longer valid, nullify it
        if not choice in experiment_choices:
            choice = None

        if not choice:
            if random.random() >= 0.1:
                # Join the best performing choice
                default_choice = experiment.get_default_choice()

                if default_choice:
                    choice = default_choice

            if not choice and len(experiment_choices) > 0:
                # Join a random choice
                choice = random.choice(experiment_choices)

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
        redis = self.redis()
        choice = self.get_experiment_choice(name)
        experiment = oz.plugins.bandit.Experiment(redis, name)

        if choice:
            experiment.add_reward(choice)

    def choose_experiment_callback(self, name, *args, **kwargs):
        """
        Helper method that takes in a dict of choice names to callbacks. A
        choice is selected for the user, and the associated callback is
        executed with the specified `args` and `kwargs`. If the callback
        returns `True`, the choice is marked successful.
        """

        choice = self.choose_experiment(name)
        result = choices[choice](*args, **kwargs)
        if result == True: self.experiment_success(name)
        return choice
