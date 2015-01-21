"""Actions for the core plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import tornado.web
import tornado.wsgi
import tornado.ioloop
import tornado.httpserver
import wsgiref.simple_server
import oz
import sys
import shutil
import unittest
import os
import functools
import re

VALID_PROJECT_NAME = re.compile(r"^\w+$")

def check_path(path, otherwise):
    """
    Checks if a path exists. If it does, print a warning message; if not,
    execute the `otherwise` callback argument.
    """

    if os.path.exists(path):
        print("WARNING: Path '%s' already exists; skipping" % path)
    else:
        otherwise(path)

def config_maker(project_name, path):
    """Creates a config file based on the project name"""

    with open(skeleton_path("config.py"), "r") as config_source:
        config_content = config_source.read()

    config_content = config_content.replace("__PROJECT_NAME__", project_name)

    with open(path, "w") as config_dest:
        config_dest.write(config_content)

def skeleton_path(parts):
    """Gets the path to a skeleton asset"""
    return os.path.join(os.path.dirname(oz.__file__), "skeleton", parts)

@oz.action
def init(project_name):
    """Creates a new project"""

    if not VALID_PROJECT_NAME.match(project_name):
        print("Invalid project name. It may only contain letters, numbers and underscores.", file=sys.stderr)
        return

    check_path(project_name, functools.partial(shutil.copytree, skeleton_path("plugin")))
    check_path("static", os.mkdir)
    check_path("templates", os.mkdir)
    check_path("config.py", functools.partial(config_maker, project_name))

@oz.action
def server():
    """Runs the server"""

    if oz.settings["wsgi_mode"]:
        application = tornado.wsgi.WSGIApplication(oz._routes, **oz.settings)
        srv = wsgiref.simple_server.make_server("", oz.settings["port"], application)
        srv.serve_forever()
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

        srv = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
        srv.bind(oz.settings["port"])

        if oz.settings["debug"]:
            if oz.settings["server_workers"] != 1:
                print("WARNING: Debug is enabled, but multiple server workers have been configured. Only one server worker can run in debug mode.")

            srv.start(1)
        else:
            # Forks multiple sub-processes
            srv.start(oz.settings["server_workers"])
        
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

    for t in oz._tests:
        if not filters_set or t.__name__ in filters_set:
            # Add the class to the suite
            child_suite = unittest.makeSuite(t, "test")
            suite.addTest(child_suite)

    res = unittest.TextTestRunner().run(suite)
    return 1 if len(res.errors) > 0 or len(res.failures) > 0 else 0
