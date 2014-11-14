import sys

project_name = "oz_tests"

# Do not use the AWS CDN plugin if this is python 3.x, as boto is not
# python 3.x compatible
if sys.version_info >= (3,):
    plugins = [
        "oz.plugins.bandit",
        "oz.plugins.blinks",
        "oz.plugins.core",
        "oz.plugins.json_api",
        "oz.plugins.redis",
        "oz.plugins.redis_sessions",
        "oz.plugins.sqlalchemy",
        "oz.plugins.error_pages",
        project_name,
    ]
else:
    plugins = [
        "oz.plugins.aws_cdn",
        "oz.plugins.bandit",
        "oz.plugins.blinks",
        "oz.plugins.core",
        "oz.plugins.json_api",
        "oz.plugins.redis",
        "oz.plugins.redis_sessions",
        "oz.plugins.sqlalchemy",
        "oz.plugins.error_pages",
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
