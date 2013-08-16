from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    debug = dict(type=bool, default=False, help="Debug mode. Stack traces will be displayed on errors, and the server will automatically reload when server code is changed. This should not be enabled in production."),
    port = dict(type=int, default=8000, help="The port on which to run the server."),
    static_path = dict(type=str, default=None, help="Path to the static directory. If set to None, then static asset hosting is disabled."),
    template_path = dict(type=str, default="templates", help="Path to the templates directory."),
    xsrf_cookies = dict(type=bool, default=False, help="Enable cookies that prevent XSRF attacks."),
    cookie_secret = dict(type=str, help="Secret used for secure cookies. Required if you set xsrf_cookies=True."),
    gzip = dict(type=bool, help="Enables gzip output."),
    wsgi_mode = dict(type=bool, default=False, help="Use WSGI mode."),
    server_workers = dict(type=int, default=1, help="The number of server workers to run concurrently.")
)