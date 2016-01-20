from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    use_secure_cookie=dict(type=bool, help="Set secure cookies with the secure flag"),
    use_hsts=dict(type=bool, help="Set the Strict-Transport-Security header")
)