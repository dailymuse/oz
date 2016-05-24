from setuptools import setup

version = "0.6.0"

setup(
    name = "Oz",
    version = version,
    description = "A batteries-included web framework built on Tornado",
    author = "Yusuf Simonson",
    author_email = 'yusuf@themuse.com',
    url = "http://github.com/dailymuse/oz",
    zip_safe = False,
    
    packages = [
        "oz",
        "oz.aws_cdn",
        "oz.aws_cdn.tests",
        "oz.bandit",
        "oz.bandit.tests",
        "oz.blinks",
        "oz.blinks.tests",
        "oz.core",
        "oz.json_api",
        "oz.json_api.tests",
        "oz.redis",
        "oz.redis_sessions",
        "oz.redis_sessions.tests",
        "oz.sqlalchemy",
        "oz.error_pages",
        "oz.error_pages.tests",
    ],

    package_data = {
        "oz": [
            "skeleton/*.py",
            "skeleton/plugin/*.py",
            "skeleton/plugin/tests/*.py",
        ]
    },

    install_requires = [
        "tornado>=3.1",
        "optfn==0.4.1"
    ],

    extras_require = {
        "oz.aws_cdn": ["boto>=2.9.7"],
        "oz.redis": ["redis>=2.6.0"],
        "oz.sqlalchemy": ["sqlalchemy>=0.7.8"]
    },

    entry_points = {
        "console_scripts": ["oz = oz.cli:main"]
    }
)
