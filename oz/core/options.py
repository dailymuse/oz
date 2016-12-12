"""Options for the core plugin"""

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
    server_workers = dict(type=int, default=1, help="The number of server workers to run concurrently."),
    body_timeout = dict(type=int, default=None, help="How long to wait in seconds while reading the request body"),
    xheaders = dict(type=bool, default=False, help="Determine remote_ip from X-Remote-Ip/X-Forwarded-For headers"),
    ssl_cert_file = dict(type=str, default=None, help="The SSL certificate file. If unspecified, SSL support will be disabled."),
    ssl_key_file = dict(type=str, default=None, help="The SSL key file. If unspecified, SSL support will be disabled."),
    ssl_ca_certs = dict(type=str, default=None, help="SSL CA certificates file."),
    ssl_cert_reqs = dict(type=int, default=0, help="Whether certificates are required from the other side of the connection. 0 = certificates ignored, 1 = certificates optional, 2 = certificates required."),
    server_type = dict(type=str, default=None, help="By default, tornado will be started with the default ioloop. If this is set, a custom server can be used instead. Valid options: 'asyncio', 'twisted' or 'wsgi'."),
    use_secure_cookie=dict(type=bool, default=False, help="Set secure cookies with the secure flag"),
    use_hsts=dict(type=bool, default=False, help="Set the Strict-Transport-Security header"),
    use_graceful_shutdown=dict(type=bool, default=True, help="Stop the server gracefully"),
    graceful_shutdown_timeout=dict(type=int, default=5, help="Number of seconds to wait before forcing the server to stop")
)
