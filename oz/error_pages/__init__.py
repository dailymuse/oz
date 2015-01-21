"""The error pages plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from .middleware import *
from .uimodules import *
from .options import *
from .tests import *

import traceback
import base64
import pprint
import linecache

class DebugBreakException(Exception):
    """Raise this to break into the debugger during an HTTP request"""
    pass

def debug():
    """Used to create debug breakpoints in code"""
    raise DebugBreakException()

class ErrorFrame(object):
    """Holds information about a function call in a traceback"""

    def __init__(self, tback, filename, function, lineno, vars, id, pre_context, context_line, post_context, pre_context_lineno):
        self.tback = tback
        self.filename = filename
        self.function = function
        self.lineno = lineno
        self.vars = vars
        self.id = id
        self.pre_context = pre_context
        self.context_line = context_line
        self.post_context = post_context
        self.pre_context_lineno = pre_context_lineno

def get_lines_from_file(filename, lineno, context_lines):
    """
    Returns context_lines before and after lineno from file.
    Returns (pre_context_lineno, pre_context, context_line, post_context).
    """

    get_lines = lambda s, e: [linecache.getline(filename, l).rstrip() for l in range(s, e)]

    lower_bound = max(1, lineno - context_lines)
    upper_bound = lineno + context_lines
    linecache.checkcache(filename)
    pre_context = get_lines(lower_bound, lineno)
    context_line = linecache.getline(filename, lineno).rstrip()
    post_context = get_lines(lineno + 1, upper_bound)
    return lower_bound, pre_context, context_line, post_context

def get_frames(tback, is_breakpoint):
    """Builds a list of ErrorFrame objects from a traceback"""

    frames = []

    while tback is not None:
        if tback.tb_next == None and is_breakpoint:
            break

        filename = tback.tb_frame.f_code.co_filename
        function = tback.tb_frame.f_code.co_name
        context = tback.tb_frame.f_locals
        lineno = tback.tb_lineno - 1
        tback_id = id(tback)
        pre_context_lineno, pre_context, context_line, post_context = get_lines_from_file(filename, lineno + 1, 7)
        frames.append(ErrorFrame(tback, filename, function, lineno, context, tback_id, pre_context, context_line, post_context, pre_context_lineno))
        tback = tback.tb_next

    return frames

def prettify_object(obj):
    """Makes a pretty string for an object for nice output"""

    try:
        return pprint.pformat(str(obj))
    except UnicodeDecodeError as e:
        raise
    except Exception as e:
        return "[could not display: <%s: %s>]" % (e.__class__.__name__, str(e))
