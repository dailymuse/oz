"""Middleware for the secure cookie plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz


class SecureMiddleware(object):
    """Middleware to set secure and httponly flags for secure cookies"""

    def prepare(self):
        if oz.settings["use_hsts"]:
            self.set_header("Strict-Transport-Security", "max-age=2592000; includeSubDomains")

        super(SecureMiddleware, self).prepare()

    def set_secure_cookie(self, name, value, **kwargs):
        if oz.settings["use_secure_cookie"]:
            if "secure" not in kwargs:
                kwargs["secure"] = True
            if "httponly" not in kwargs:
                kwargs["httponly"] = True

        super(SecureMiddleware, self).set_secure_cookie(name, value, **kwargs)