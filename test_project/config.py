import sys

project_name = "oz_tests"

# Do not use the AWS CDN plugin if this is python 3.x, as boto is not
# python 3.x compatible
if sys.version_info >= (3,):
    plugins = [
        "oz.bandit",
        "oz.blinks",
        "oz.core",
        "oz.json_api",
        "oz.redis",
        "oz.redis_sessions",
        "oz.sqlalchemy",
        "oz.error_pages",
        project_name,
    ]
else:
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
        project_name,
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
