from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.app
import re
import oz.plugins.json_api
from tornado import escape
import traceback

API_ERROR_CODE_MAP = { 404: "Not found", 500: "Server error" }
CALLBACK_VALIDATOR = re.compile('^[$A-Za-z_][0-9A-Za-z_$]*$')

class ApiMiddleware(object):
    def __init__(self):
        super(ApiMiddleware, self).__init__()
        self._decoded_body = None
        self.trigger_listener("write_error", self._api_on_write_error)

    def _api_on_write_error(self, status_code, **kwargs):
        """
        Catches errors and renders it as a JSON message. Adds the traceback if
        debug is enabled.
        """

        return_error = { "code": self.get_status() }
        exc_info = kwargs.get("exc_info")

        if exc_info and isinstance(exc_info[1], oz.plugins.json_api.ApiError):
            return_error["error"] = exc_info[1].message
        else:
            return_error["error"] = API_ERROR_CODE_MAP.get(self.get_status(), "Unknown error")

        if oz.app.settings.get("debug"):
            return_error["trace"] = "".join(traceback.format_exception(*exc_info))

        self.finish(return_error)
        return oz.break_trigger

    def respond(self, obj):
        """Gives a response JSON(P) message"""

        # Get the callback argument if JSONP is allowed
        callback = self.get_argument("callback", None) if oz.app.settings["allow_jsonp"] else None

        # We're pretty strict with what callback names are allowed, just in case
        if callback and not CALLBACK_VALIDATOR.match(callback):
            raise oz.plugins.json_api.ApiError("Invalid callback identifier - only functions with ASCII characters are allowed")

        # Provide the response in a different manner depending on whether a
        # JSONP callback is specified
        json = escape.json_encode(obj)

        if callback:
            self.set_header("Content-Type", "application/javascript; charset=UTF-8")
            self.finish("%s(%s)" % (callback, json))
        else:
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(json)

    def body(self):
        """Gets the JSON body of the request"""

        if self._decoded_body == None:
            # Try to decode the JSON body. But raise an error if the
            # content-type is unexpected, or the JSON is invalid.

            raw_content_type = self.request.headers.get("content-type") or ""
            content_type = raw_content_type.split(";")[0].strip().lower()

            if content_type == "application/json":
                try:
                    self._decoded_body = escape.json_decode(self.request.body)
                except:
                    raise oz.plugins.json_api.ApiError("Bad JSON body")
            else:
                raise oz.plugins.json_api.ApiError("JSON body expected")

        return self._decoded_body
