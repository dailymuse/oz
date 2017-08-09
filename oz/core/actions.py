"""Actions for the core plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import wsgiref.simple_server
import signal
import time
import sys
import shutil
import unittest
import os
import functools
import re

import tornado.web
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.log

import oz

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

    tornado.log.enable_pretty_logging()

    # Get and validate the server_type
    server_type = oz.settings["server_type"]
    if server_type not in [None, "wsgi", "asyncio", "twisted"]:
        raise Exception("Unknown server type: %s" % server_type)

    # Install the correct ioloop if necessary
    if server_type == "asyncio":
        from tornado.platform.asyncio import AsyncIOMainLoop
        AsyncIOMainLoop().install()
    elif server_type == "twisted":
        from tornado.platform.twisted import TwistedIOLoop
        TwistedIOLoop().install()

    if server_type == "wsgi":
        wsgi_app = tornado.wsgi.WSGIApplication(oz._routes, **oz.settings)
        wsgi_srv = wsgiref.simple_server.make_server("", oz.settings["port"], wsgi_app)
        wsgi_srv.serve_forever()
    else:
        web_app = tornado.web.Application(oz._routes, **oz.settings)

        if oz.settings["ssl_cert_file"] != None and oz.settings["ssl_key_file"] != None:
            ssl_options = {
                "certfile": oz.settings["ssl_cert_file"],
                "keyfile": oz.settings["ssl_key_file"],
                "cert_reqs": oz.settings["ssl_cert_reqs"],
                "ca_certs": oz.settings["ssl_ca_certs"]
            }
        else:
            ssl_options = None

        http_srv = tornado.httpserver.HTTPServer(
            web_app,
            ssl_options=ssl_options,
            body_timeout=oz.settings["body_timeout"],
            xheaders=oz.settings["xheaders"]
        )

        http_srv.bind(oz.settings["port"])

        server_workers = oz.settings["server_workers"]

        if server_workers > 1:
            if oz.settings["debug"]:
                print("WARNING: Debug is enabled, but multiple server workers have been configured. Only one server worker can run in debug mode.")
                server_workers = 1
            elif (server_type == "asyncio" or server_type == "twisted"):
                print("WARNING: A non-default server type is being used, but multiple server workers have been configured. Only one server worker can run on a non-default server type.")
                server_workers = 1

        # Forks multiple sub-processes if server_workers > 1
        http_srv.start(server_workers)

        # Registers signal handles for graceful server shutdown
        if oz.settings.get("use_graceful_shutdown"):
            if server_type == "asyncio" or server_type == "twisted":
                print("WARNING: Cannot enable graceful shutdown for asyncio or twisted server types.")
            else:
                # NOTE: Do not expect any logging to with certain tools (e.g., invoker),
                # because they may quiet logs on SIGINT/SIGTERM
                signal.signal(signal.SIGTERM, functools.partial(_shutdown_tornado_ioloop, http_srv))
                signal.signal(signal.SIGINT, functools.partial(_shutdown_tornado_ioloop, http_srv))

        # Starts the ioloops
        if server_type == "asyncio":
            import asyncio
            asyncio.get_event_loop().run_forever()
        elif server_type == "twisted":
            from twisted.internet import reactor
            reactor.run()
        else:
            from tornado import ioloop
            ioloop.IOLoop.instance().start()

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

def _shutdown_tornado_ioloop(http_srv, sig, frame):
    io_loop = tornado.ioloop.IOLoop.instance()

    def stop_loop(deadline_seconds):
        now = time.time()
        if now < deadline_seconds and io_loop._callbacks:
            io_loop.add_timeout(now + 1, stop_loop, deadline_seconds)
        else:
            io_loop.stop()

    def shutdown():
        tornado.log.app_log.info("Shutting down server....")
        http_srv.stop()
        stop_loop(time.time() + oz.settings.get("graceful_shutdown_timeout", 5))

    tornado.log.app_log.warning("Received %s", sig)
    io_loop.add_callback_from_signal(shutdown)
