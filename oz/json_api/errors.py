"""Errors for the JSON API plugin"""

import tornado.web

class ApiError(tornado.web.HTTPError):
    """Exception for API-based errors"""

    def __init__(self, message, code=400):
        super(ApiError, self).__init__(code)
        self.message = message
