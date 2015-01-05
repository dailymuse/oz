import oz
import oz.app
import oz.admin_actions
import sys
import optfn

def main():
    """
    Script for running actions that are not part of a project's manager.py
    """

    try:
        import config
    except ImportError:
        # Hack to notify the user that config.py wasn't found if they're not
        # running a built-in action
        if len(sys.argv) > 1 and sys.argv[1] not in ["init", "explore"]:
            raise
        
        config = None

    actions = [oz.admin_actions.init, oz.admin_actions.explore]

    if config:
        oz.initialize(config)
        actions.extend(oz.app.actions.values())

    retr = optfn.run(actions)

    if retr == optfn.ERROR_RETURN_CODE:
        sys.exit(-1)
    elif retr == None:
        sys.exit(0)
    elif isinstance(retr, int):
        sys.exit(retr)
    else:
        raise Exception("Unexpected return value from action: %s" % retr)