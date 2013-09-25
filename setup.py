from setuptools import setup

version = "0.1"

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
        "oz.admin_actions",
        "oz.plugins",
        "oz.plugins.aws_cdn",
        "oz.plugins.aws_cdn.tests",
        "oz.plugins.bandit",
        "oz.plugins.bandit.tests",
        "oz.plugins.blinks",
        "oz.plugins.blinks.tests",
        "oz.plugins.core",
        "oz.plugins.json_api",
        "oz.plugins.json_api.tests",
        "oz.plugins.redis",
        "oz.plugins.redis_sessions",
        "oz.plugins.redis_sessions.tests",
        "oz.plugins.sqlalchemy",
    ],
    
    scripts = ["scripts/oz"],

    package_data = {
        "oz": [
            "plugins/bandit/assets/*",
            "skeleton/*.py",
            "skeleton/plugin/*.py",
            "skeleton/plugin/tests/*.py",
        ]
    },

    install_requires = [
        "tornado>=2.4.1",
        "optfn==0.4.1"
    ],

    extras_require = {
        "oz.plugins.aws_cdn": ["boto>=2.9.7"],
        "oz.plugins.redis": ["redis>=2.6.0"],
        "oz.plugins.sqlalchemy": ["sqlalchemy>=0.7.8"]
    }
)
