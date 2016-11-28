"""Oz"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import types
import collections
import tornado.web
import tornado.options
import tornado.util
import tornado.log
import inspect
import functools
import os

# On trigger execution, trigger listeners can return this to notify the
# request handler to cancel execution of the next functions in the trigger
# chain.
break_trigger = object()

# Mapping of action name -> callback
_actions = {}

# Mapping of uimodule name -> class
_uimodules = {}

# List of routes
_routes = []

# List of test classes
_tests = []

# Mapping of setting name -> value
settings = {}

def _add_to_dict(t, container, name, value):
    """
    Adds an item to a dictionary, or raises an exception if an item with the
    specified key already exists in the dictionary.
    """

    if name in container:
        raise Exception("%s '%s' already exists" % (t, name))
    else:
        container[name] = value

def action(fun):
    """Exposes an action"""
    _add_to_dict("Action", _actions, fun.__name__, fun)
    return fun

def uimodule(cls):
    """Exposes a UIModule"""
    _add_to_dict("UIModules", _uimodules, cls.__name__, cls)
    return cls

def route(new_route):
    """Exposes a route"""
    _routes.append(new_route)

def routes(*new_routes):
    """Exposes a list of routes"""
    _routes.extend(new_routes)

def option(name, **args):
    """Exposes an option"""
    tornado.options.define(name, **args)

def options(**kwargs):
    """Exposes several options"""
    for name, args in kwargs.items():
        option(name, **args)

def test(cls):
    """Exposes a unit test class, to be run on the `test` action."""
    _tests.append(cls)
    return cls

def plugin(namespace):
    """Loads an oz plugin"""
    __import__(namespace, globals(), locals(), [], 0)

class RequestHandler(tornado.web.RequestHandler):
    """
    Builds on top of tornado's RequestHandler to provide template helpers and
    triggers
    """

    def __init__(self, *args, **kwargs):
        self._template_helpers = {}
        self._triggers = collections.defaultdict(lambda: [])
        super(RequestHandler, self).__init__(*args, **kwargs)

    def template_helper(self, name, callback):
        """Adds a template helper"""
        _add_to_dict("Template helper", self._template_helpers, name, callback)

    def trigger_listener(self, name, callback):
        """Adds a trigger listener"""
        self._triggers[name].append(callback)

    def trigger(self, name, *args, **kwargs):
        """
        Triggers an event to run through middleware. This method will execute
        a chain of relevant trigger callbacks, until one of the callbacks
        returns the `break_trigger`.
        """

        # Relevant middleware is cached so we don't have to rediscover it
        # every time. Fetch the cached value if possible.

        listeners = self._triggers.get(name, [])

        # Execute each piece of middleware
        for listener in listeners:
            result = listener(*args, **kwargs)

            if result == break_trigger:
                return False

        return True

    def get_template_namespace(self):
        # Start with the default namespace
        namespace = super(RequestHandler, self).get_template_namespace()

        # Add the template helpers
        namespace.update(self._template_helpers)

        return namespace

    def initialize(self, **kwargs):
        self.trigger("initialize", **kwargs)

    def prepare(self):
        self.trigger("prepare")

    def on_finish(self):
        self.trigger("on_finish")

    def on_connection_close(self):
        self.trigger("on_connection_close")

    def write_error(self, *args, **kwargs):
        # Call super's implementation of `write_error` unless we hit a
        # `break_trigger`.
        if self.trigger("write_error", *args, **kwargs):
            super(RequestHandler, self).write_error(*args, **kwargs)

def initialize(config=None):
    """Initializes oz"""

    # Load the config file
    if config == None:
        config = {}
        config_source = None

        try:
            with open(os.environ.get("OZ_CONFIG", "config.py")) as f:
                config_source = f.read()
        except Exception:
            tornado.log.gen_log.info("Could not read config.py", exc_info=True)

        if config_source != None:
            tornado.util.exec_in(config_source, config, config)

    # Load the plugins
    for p in config.get("plugins", ["oz.core"]):
        plugin(p)

    # Set the options
    for key, value in config.get("app_options", {}).items():
        setattr(tornado.options.options, key, value)

    # Generate the application settings
    global settings
    settings = tornado.options.options.as_dict()
    settings["ui_modules"] = _uimodules
    settings["project_name"] = config.get("project_name")
