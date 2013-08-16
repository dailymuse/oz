from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import tornado.web
import tornado.wsgi
import tornado.ioloop
import tornado.httpserver
import wsgiref.simple_server
import oz
import oz.app
import oz.testing
import sys
import shutil
import unittest

@oz.action
def server():
    """Runs the server"""

    settings = oz.app.settings

    if settings["wsgi_mode"]:
        application = tornado.wsgi.WSGIApplication(oz.app.routes, **settings)
        server = wsgiref.simple_server.make_server("", settings["port"], application)
        server.serve_forever()
    else:
        application = tornado.web.Application(oz.app.routes, **settings)
        server = tornado.httpserver.HTTPServer(application)
        server.bind(settings["port"])

        if settings["debug"]:
            if settings["server_workers"] != 1:
                print >> sys.stderr, "WARNING: Debug is enabled, but multiple server workers have been configured. Only one server worker can run in debug mode."

            server.start(1)
        else:
            # Forks multiple sub-processes
            server.start(settings["server_workers"])
        
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
        settings=oz.app.settings,
        actions=oz.app.actions,
        uimodules=oz.app.uimodules,
        routes=oz.app.routes,
    ))

@oz.action
def test(*filters):
    """Runs the unit tests"""

    suite = unittest.TestSuite()
    filters_set = set(filters)

    for test in oz.app.tests:
        if not filters_set or test.__name__ in filters_set:
            # Add the class to the suite
            child_suite = unittest.makeSuite(test, "test")
            suite.addTest(child_suite)

    res = unittest.TextTestRunner().run(suite)
    return 1 if len(res.errors) > 0 or len(res.failures) > 0 else 0
