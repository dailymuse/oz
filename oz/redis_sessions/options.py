"""Options for the redis sessions plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    session_salt = dict(type=str, help="Salt used for session security"),
    session_time = dict(type=int, help="Number of seconds of session inactivity before timeout")
)
