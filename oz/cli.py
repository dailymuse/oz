from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import sys
import optfn
import inspect
import os
import functools
import shutil
import re

VALID_PROJECT_NAME = re.compile("^\w+$")

def _explore_dict(d):
    if len(d):
        for value in d.values():
            doc = getattr(value, "__doc__")

            if doc:
                print("- %s: %s" % (value.__name__, doc))
            else:
                print("- %s" % value.__name__)
    else:
        print("  None")

def _check_path(path, otherwise):
    """
    Checks if a path exists. If it does, print a warning message; if not,
    execute the `otherwise` callback argument.
    """

    if os.path.exists(path):
        print("WARNING: Path '%s' already exists; skipping" % path)
    else:
        otherwise(path)

def _config_maker(project_name, path):
    """Creates a config file based on the project name"""

    with open(_skeleton_path("config.py"), "r") as config_source:
        config_content = config_source.read()

    config_content = config_content.replace("__PROJECT_NAME__", project_name)

    with open(path, "w") as config_dest:
        config_dest.write(config_content)

def _skeleton_path(parts):
    """Gets the path to a skeleton asset"""
    return os.path.join(os.path.dirname(oz.__file__), "skeleton", parts)

def explore(plugin_name):
    """
    Explores a given plugin, printing out its actions, UIModules, middleware,
    routes, options and tests
    """

    module = __import__(plugin_name, globals(), locals(), [], -1)

    for sub_module_name in plugin_name.split(".")[1:]:
       module = getattr(module, sub_module_name)

    print("Actions")
    _explore_dict(oz._actions)

    print("\nUIModules")
    _explore_dict(oz._uimodules)

    print("\nRoutes")
    if oz._routes:
        for route in oz._routes:
            print("- %s" % route[0])
            print("  - request handler: %s" % route[1])

            if len(route) > 2:
                print("  - request handler initialization args: %s" % route[2])
    else:
        print("  None")

    print("\nOptions")
    if oz._options:
        for option_name, option_params in oz._options.items():
            print("- %s" % option_name)

            for option_param_name, option_param in option_params.items():
                print("  - %s: %s" % (option_param_name, option_param))
    else:
        print("  None")

    print("\nTests")
    if oz._tests:
        for test in oz._tests:
            print("- %s" % test.__name__)
    else:
        print("  None")

def init(project_name):
    """Creates a new project"""

    if not VALID_PROJECT_NAME.match(project_name):
        print("Invalid project name. It may only contain letters, numbers and underscores.", file=sys.stderr)
        return

    _check_path(project_name, functools.partial(shutil.copytree, _skeleton_path("plugin")))
    _check_path("static", os.mkdir)
    _check_path("templates", os.mkdir)
    _check_path("config.py", functools.partial(_config_maker, project_name))

def main():
    """
    Script for running actions that are not part of a project's manager.py
    """

    sys.path.insert(0, ".")

    try:
        import config
    except ImportError:
        # Hack to notify the user that config.py wasn't found if they're not
        # running a built-in action
        if len(sys.argv) > 1 and sys.argv[1] not in ["init", "explore"]:
            raise
        
        config = None

    actions = [init, explore]

    if config:
        oz.initialize(config)
        actions.extend(oz._actions.values())

    retr = optfn.run(actions)

    if retr == optfn.ERROR_RETURN_CODE:
        sys.exit(-1)
    elif retr == None:
        sys.exit(0)
    elif isinstance(retr, int):
        sys.exit(retr)
    else:
        raise Exception("Unexpected return value from action: %s" % retr)