"""Options for the JSON API plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
oz.option("allow_jsonp", type=bool, default=True, help="Whether to allow for JSONP requests")
