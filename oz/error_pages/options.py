"""Options for the error pages middleware"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    error_pages_template = dict(type=str, default="error_page.html", help="Special error page to render when an error occurs and debug is True. This should come from the error_pages plugin source code."),
)
