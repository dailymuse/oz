"""Middleware for the blinks plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from tornado import escape

class BlinkMiddleware(object):
    """Adds flask-like blink functionality"""

    def __init__(self):
        super(BlinkMiddleware, self).__init__()
        self.template_helper("get_blink", self.get_blink)

    def get_blink_cookie(self, name):
        """Gets a blink cookie value"""
        value = self.get_cookie(name)

        if value != None:
            self.clear_cookie(name)
            return escape.url_unescape(value)

    def set_blink(self, message, type="info"):
        """
        Sets the blink, a one-time transactional message that is shown on the
        next page load
        """
        self.set_cookie("blink_message", escape.url_escape(message), httponly=True)
        self.set_cookie("blink_type", escape.url_escape(type), httponly=True)

    def get_blink(self):
        """Gets the blink message and type"""
        return self.get_blink_cookie("blink_message"), self.get_blink_cookie("blink_type")
