import oz
import binascii
import tornado.web
from tornado.escape import xhtml_escape

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs

class Subresource(tornado.web.UIModule):
    def get_integrity(self, url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        # cdn_static_url currently appends ?v=None to the URL if there is no
        # known hash of the. Default to this if `v` is somehow not defined as
        # well.
        v_arg = query.get("v", ["None"])[0]

        if v_arg == "None":
            return None
        else:
            # v_arg contains the hash in hex encoding - we need to convert it
            # to base64. This roundabout method should work in both python 2
            # 3.
            return "sha256-%s" % binascii.b2a_base64(bytearray.fromhex(v_arg)).strip().decode("utf8")

@oz.uimodule
class Script(Subresource):
    def render(self, path, sip=True, crossorigin="anonymous", **attrs):
        url = self.handler.cdn_static_url(path)

        if sip:
            integrity = self.get_integrity(url)

            if integrity and "integrity" not in attrs:
                attrs["integrity"] = integrity
            
            if "crossorigin" not in attrs:
                attrs["crossorigin"] = crossorigin

        if "src" not in attrs:
            attrs["src"] = url

        attr_strs = ['%s="%s"' % (xhtml_escape(k), xhtml_escape(v)) for (k, v) in attrs.items()]
        return "<script %s></script>" % " ".join(attr_strs)

@oz.uimodule
class Stylesheet(Subresource):
    def render(self, path, sip=True, crossorigin="anonymous", **attrs):
        url = self.handler.cdn_static_url(path)

        if sip:
            integrity = self.get_integrity(url)
            
            if integrity and "integrity" not in attrs:
                attrs["integrity"] = integrity
            
            if "crossorigin" not in attrs:
                attrs["crossorigin"] = crossorigin

        if "rel" not in attrs:
            attrs["rel"] = "stylesheet"
        if "href" not in attrs:
            attrs["href"] = url

        attr_strs = ['%s="%s"' % (xhtml_escape(k), xhtml_escape(v)) for (k, v) in attrs.items()]
        return "<link %s />" % " ".join(attr_strs)
