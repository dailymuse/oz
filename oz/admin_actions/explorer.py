from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz.app
import inspect
import oz

def explore_dict(d):
    if len(d):
        for value in d.values():
            doc = getattr(value, "__doc__")

            if doc:
                print("- %s: %s" % (value.__name__, doc))
            else:
                print("- %s" % value.__name__)
    else:
        print("  None")

def get_classes(module, subclass_of):
    for _, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, subclass_of):
            yield obj

def explore(plugin_name):
    """
    Explores a given plugin, printing out its actions, UIModules, middleware,
    routes, options and tests
    """

    module = __import__(plugin_name, globals(), locals(), [], -1)

    for sub_module_name in plugin_name.split(".")[1:]:
       module = getattr(module, sub_module_name)

    print("Actions")
    explore_dict(oz.app.actions)

    print("\nUIModules")
    explore_dict(oz.app.uimodules)

    print("\nRoutes")
    if oz.app.routes:
        for route in oz.app.routes:
            print("- %s" % route[0])
            print("  - request handler: %s" % route[1])

            if len(route) > 2:
                print("  - request handler initialization args: %s" % route[2])
    else:
        print("  None")

    print("\nOptions")
    if oz.app.options:
        for option_name, option_params in oz.app.options.items():
            print("- %s" % option_name)

            for option_param_name, option_param in option_params.items():
                print("  - %s: %s" % (option_param_name, option_param))
    else:
        print("  None")

    print("\nTests")
    if oz.app.tests:
        for test in oz.app.tests:
            print("- %s" % test.__name__)
    else:
        print("  None")
