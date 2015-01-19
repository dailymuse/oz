import sys

project_name = "oz_tests"

plugins = [
    "oz.aws_cdn",
    "oz.bandit",
    "oz.blinks",
    "oz.core",
    "oz.json_api",
    "oz.redis",
    "oz.redis_sessions",
    "oz.sqlalchemy",
    "oz.error_pages",
]

app_options = dict(
    port = 8000,
    debug = True,
    db = "sqlite:///oz_tests.db",
    static_path = "static",
    template_path = "templates",
    xsrf_cookies = False,
    gzip = False,
    session_salt = "some salt",
    cookie_secret = "abcdef"
)