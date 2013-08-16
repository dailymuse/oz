"""Defines application routes"""

import oz
import handlers

oz.routes(
    (r"^/file/([^/]+)$", handlers.FileHandler),
    (r"^/copy-file/([^/]+)/([^/]+)$", handlers.FileCopyingHandler),
    (r"^/cache-buster/([^/]+)$", handlers.CacheBusterHandler),

    (r"^/experiment/(\w+)$", handlers.ExperimentHandler),

    (r"^/blink$", handlers.BlinkHandler),

    (r"^/api/echo$", handlers.EchoApiHandler),
    (r"^/api/error/normal$", handlers.NormalErrorApiHandler),
    (r"^/api/error/unexpected$", handlers.UnexpectedErrorApiHandler),

    (r"^/db/(.+)", handlers.DatabaseHandler),

    (r"^/session$", handlers.SessionHandler),
    (r"^/session/(.+)", handlers.SessionValueHandler),
)