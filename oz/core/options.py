"""Options for the core plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals
import sys

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
    server_workers = dict(type=int, default=1, help="The number of server workers to run concurrently."),
    xml_test_output = dict(type=bool, default=False, help="Output testing results in JUnit-style XML format instead of standard text format"),
    test_output_file = dict(type=str, default=sys.stdout, help="The file to write test output to"),
    body_timeout = dict(type=int, default=None, help="How long to wait in seconds while reading the request body"),

    ssl_cert_file = dict(type=str, default=None, help="The SSL certificate file. If unspecified, SSL support will be disabled."),
    ssl_key_file = dict(type=str, default=None, help="The SSL key file. If unspecified, SSL support will be disabled."),
    ssl_cert_reqs = dict(type=int, default=0, help="Whether certificates are required from the other side of the connection. 0 = certificates ignored, 1 = certificates optional, 2 = certificates required."),
    ssl_ca_certs = dict(type=str, default=None, help="SSL CA certificates file.")
)