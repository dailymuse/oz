from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import os
import functools
import shutil
import re
import oz
import sys

VALID_PROJECT_NAME = re.compile("^\w+$")

def check_path(path, otherwise):
    """
    Checks if a path exists. If it does, print a warning message; if not,
    execute the `otherwise` callback argument.
    """

    if os.path.exists(path):
        print("WARNING: Path '%s' already exists; skipping" % path)
    else:
        otherwise(path)

def config_maker(project_name, path):
    """Creates a config file based on the project name"""

    with open(skeleton_path("config.py"), "r") as config_source:
        config_content = config_source.read()

    config_content = config_content.replace("__PROJECT_NAME__", project_name)

    with open(path, "w") as config_dest:
        config_dest.write(config_content)

def skeleton_path(parts):
    """Gets the path to a skeleton asset"""
    return os.path.join(os.path.dirname(oz.__file__), "skeleton", parts)

def init(project_name):
    """Creates a new project"""

    if not VALID_PROJECT_NAME.match(project_name):
        print("Invalid project name. It may only contain letters, numbers and underscores.", file=sys.stderr)
        return

    check_path(project_name, functools.partial(shutil.copytree, skeleton_path("plugin")))
    check_path("static", os.mkdir)
    check_path("templates", os.mkdir)
    check_path("config.py", functools.partial(config_maker, project_name))
