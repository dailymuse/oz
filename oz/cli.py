from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import optfn
import sys

def main():
    oz.initialize()
    retr = optfn.run(list(oz._actions.values()))

    if retr == optfn.ERROR_RETURN_CODE:
        sys.exit(-1)
    elif retr == None:
        sys.exit(0)
    elif isinstance(retr, int):
        sys.exit(retr)
    else:
        raise Exception("Unexpected return value from action: %s" % retr)
