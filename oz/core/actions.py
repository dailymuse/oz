from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import tornado.web
import tornado.wsgi
import tornado.ioloop
import tornado.httpserver
import wsgiref.simple_server
import oz
import oz.testing
import sys
import shutil
import unittest
import inspect
import os
import functools
import re
from tornado import options

VALID_PROJECT_NAME = re.compile("^\w+$")

def explore_dict(d):
    if len(d):
        for value in d.values():
            doc = getattr(value, "__doc__")

            if doc:
                print("- %s: %s" % (value.__name__, doc))
            else:
                print("- %s" % value.__name__)
    else:
        print("  None")

def check_path(path, otherwise):
    """
    Checks if a path exists. If it does, print a warning message; if not,
    execute the `otherwise` callback argument.
    """

    if os.path.exists(path):
        print("WARNING: Path '%s' already exists; skipping" % path)
    else:
        otherwise(path)

@oz.action
def explore(plugin_name):
    """
    Explores a given plugin, printing out its actions, UIModules, middleware,
    routes, options and tests
    """

    oz.plugin(plugin_name)

    for sub_module_name in plugin_name.split(".")[1:]:
       module = getattr(module, sub_module_name)

    print("Actions")
    explore_dict(oz._actions)

    print("\nUIModules")
    explore_dict(oz._uimodules)

    print("\nRoutes")
    if oz._routes:
        for route in oz._routes:
            print("- %s" % route[0])
            print("  - request handler: %s" % route[1])

            if len(route) > 2:
                print("  - request handler initialization args: %s" % route[2])
    else:
        print("  None")

    print("\nOptions")
    if oz._options:
        for option_name, option_params in oz._options.items():
            print("- %s" % option_name)

            for option_param_name, option_param in option_params.items():
                print("  - %s: %s" % (option_param_name, option_param))
    else:
        print("  None")

    print("\nTests")
    if oz._tests:
        for test in oz._tests:
            print("- %s" % test.__name__)
    else:
        print("  None")

@oz.action
def init(project_name):
    """Creates a new project"""

    if not VALID_PROJECT_NAME.match(project_name):
        print("Invalid project name. It may only contain letters, numbers and underscores.", file=sys.stderr)
        return

    check_path(project_name, lambda: shutil.copytree(os.path.join(oz.__file__, "skeleton", "plugin")))
    check_path("static", os.mkdir)
    check_path("templates", os.mkdir)

@oz.action
def server():
    """Runs the server"""

    if oz.settings["wsgi_mode"]:
        application = tornado.wsgi.WSGIApplication(oz._routes, **oz.settings)
        server = wsgiref.simple_server.make_server("", oz.settings["port"], application)
        server.serve_forever()
    else:
        application = tornado.web.Application(oz._routes, **oz.settings)

        if oz.settings["ssl_cert_file"] != None and oz.settings["ssl_key_file"] != None:
            ssl_options = {
                "certfile": oz.settings["ssl_cert_file"],
                "keyfile": oz.settings["ssl_key_file"],
                "cert_reqs": oz.settings["ssl_cert_reqs"],
                "ca_certs": oz.settings["ssl_ca_certs"]
            }
        else:
            ssl_options = None

        server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
        server.bind(oz.settings["port"])

        if oz.settings["debug"]:
            if oz.settings["server_workers"] != 1:
                print("WARNING: Debug is enabled, but multiple server workers have been configured. Only one server worker can run in debug mode.")

            server.start(1)
        else:
            # Forks multiple sub-processes
            server.start(oz.settings["server_workers"])
        
        tornado.ioloop.IOLoop.instance().start()

@oz.action
def repl():
    """Runs an IPython repl with some context"""

    try:
        import IPython
    except:
        print("ERROR: IPython is not installed. Please install it to use the repl.", file=sys.stderr)
        raise

    IPython.embed(user_ns=dict(
        settings=oz.settings,
        actions=oz._actions,
        uimodules=oz._uimodules,
        routes=oz._routes,
    ))

@oz.action
def test(*filters):
    """Runs the unit tests"""

    suite = unittest.TestSuite()
    filters_set = set(filters)

    for test in oz._tests:
        if not filters_set or test.__name__ in filters_set:
            # Add the class to the suite
            child_suite = unittest.makeSuite(test, "test")
            suite.addTest(child_suite)

    res = unittest.TextTestRunner().run(suite)
    return 1 if len(res.errors) > 0 or len(res.failures) > 0 else 0
