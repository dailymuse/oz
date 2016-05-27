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
)

    res = unittest.TextTestRunner().run(suite)
    return 1 if len(res.errors) > 0 or len(res.failures) > 0 else 0
