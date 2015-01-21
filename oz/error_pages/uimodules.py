"""UIModules for the error pages plugin"""

import oz
import base64
import pprint
import oz.error_pages
import tornado.web
import tornado.escape

TABLE_FORMAT = """
<table %s %s>
    <thead>
        <tr>
            <th>Variable</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        %s
    </tbody>
</table>
"""

TABLE_ROW_FORMAT = """
<tr>
    <td>%s %s</td>
    <td class="code">%s</td>
</tr>
"""

@oz.uimodule
class DictTable(tornado.web.UIModule):
    """Renders an HTML table from a dict"""

    def render(self, d, id=None, kls=None):
        items = sorted(d.items())

        if items:
            rows = []

            for k, v in items:
                try:
                    escaped_val = tornado.escape.xhtml_escape(oz.error_pages.prettify_object(v))
                    rows.append(TABLE_ROW_FORMAT % (k, "", escaped_val))
                except UnicodeDecodeError:
                    rows.append(TABLE_ROW_FORMAT % (k, "(in base64)", base64.b64encode(v)))

            return TABLE_FORMAT % ("id='%s'" % id if id else "", "class='%s'" if kls else "", "\n".join(rows))
        else:
            return "<p>No data</p>"
