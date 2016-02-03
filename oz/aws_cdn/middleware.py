"""Middleware for aws_cdn plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz
import oz.aws_cdn

class CDNMiddleware(object):
    """Middleware functions for AWS-based static asset management"""

    def __init__(self):
        super(CDNMiddleware, self).__init__()
        self.template_helper("cdn_static_url", self.cdn_static_url)

    def cdn_static_url(self, path):
        """
        Takes a path and returns a static URL based on the CDN configuration.
        Largely a drop-in replacement for tornado's `static_url`.
        """
        return oz.aws_cdn.static_url(self.redis(), path)

    def get_cache_buster(self, path):
        """Gets the cache buster value for a given file path"""
        return oz.aws_cdn.get_cache_buster(self.redis(), path)

    def set_cache_buster(self, path, hash):
        """Sets the cache buster value for a given file path"""
        oz.aws_cdn.set_cache_buster(self.redis(), path, hash)

    def remove_cache_buster(self, path):
        """Removes the cache buster for a given file"""
        oz.aws_cdn.remove_cache_buster(self.redis(), path)

    def get_file(self, path):
        """Gets a file at the given path"""
        return oz.aws_cdn.get_file(path)

    def upload_file(self, path, contents, replace=False):
        """
        Uplodas the file to its path with the given `content`, adding the
        appropriate parent directories when needed. If the path already exists
        and `replace` is `False`, the file will not be uploaded.
        """
        f = self.get_file(path)
        f.upload(contents, replace=replace)
        self.set_cache_buster(path, f.hash())

    def copy_file(self, from_path, to_path, replace=False):
        """
        Copies a file from a given source path to a destination path, adding
        appropriate parent directories when needed. If the destination path
        already exists and `replace` is `False`, the file will not be
        uploaded.
        """
        f = self.get_file(from_path)
        self.upload_file(to_path, f.contents(), replace=replace)

    def remove_file(self, path):
        """Removes the given file"""
        f = self.get_file(path).remove()
        self.remove_cache_buster(path)
