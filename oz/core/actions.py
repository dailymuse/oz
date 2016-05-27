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

def ch