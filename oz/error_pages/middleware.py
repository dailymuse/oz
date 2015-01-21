"""Middleware for the error pages plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.error_pages
import sys

class ErrorPageMiddleware(object):
    """Middleware to show the custom error page"""

    def __init__(self):
        super(ErrorPageMiddleware, self).__init__()
        self.trigger_listener("write_error", self._on_error_page_write_error)

    def _on_error_page_write_error(self, status_code, **kwargs):
        """Replaces the default Tornado error page with a Django-styled one"""

        if oz.settings.get('debug'):
            exception_type, exception_value, tback = sys.exc_info()
            is_breakpoint = isinstance(exception_value, oz.error_pages.DebugBreakException)

            frames = oz.error_pages.get_frames(tback, is_breakpoint)
            frames.reverse()

            if is_breakpoint:
                exception_type = 'Debug breakpoint'
                exception_value = ''

            self.render(oz.settings["error_pages_template"],
                exception_type=exception_type,
                exception_value=exception_value,
                frames=frames,
                request_input=self.request.body,
                request_cookies=self.cookies,
                request_headers=self.request.headers,
                request_path=self.request.uri,
                request_method=self.request.method,
                response_output="".join(self._write_buffer),
                response_headers=self._headers,
                prettify_object=oz.error_pages.prettify_object,
            )

            return oz.break_trigger
