from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import tornado.web

from .middleware import *
from .options import *
from .tests import *

class ApiError(tornado.web.HTTPError):
    """Exception for API-based errors"""

    def __init__(self, message, code=400):
        super(ApiError, self).__init__(code)
        self.message = message