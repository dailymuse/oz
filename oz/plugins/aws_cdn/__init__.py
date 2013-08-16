from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

from boto.s3.connection import S3Connection

import os
import hashlib
import mimetypes
import oz.app

from .actions import *
from .middleware import *
from .options import *
from .tests import *

def static_url(redis, path):
    """Gets the static path for a file"""
    file_hash = get_cache_buster(redis, path)
    return "%s/%s?v=%s" % (oz.app.settings["static_host"], path, file_hash)

def get_cache_buster(redis, path):
    """Gets the cache buster value for a given file path"""
    return redis.hget("cache-buster:v1", path)

def set_cache_buster(redis, path, hash):
    """Sets the cache buster value for a given file path"""
    redis.hset("cache-buster:v1", path, hash)

def remove_cache_buster(redis, path):
    """Removes the cache buster for a given file"""
    redis.hdel("cache-buster:v1", path)

def get_bucket(s3_bucket=None):
    """Gets a bucket from specified settings"""
    settings = oz.app.settings
    s3_bucket = s3_bucket or settings["s3_bucket"]
    return S3Connection(settings["aws_access_key"], settings["aws_secret_key"]).get_bucket(s3_bucket)

def get_file(path):
    if oz.app.settings["s3_bucket"]:
        bucket = get_bucket(oz.app.settings["s3_bucket"])
        return S3File(bucket.new_key(path))
    else:
        return LocalFile(oz.app.settings["static_path"], path)

class CDNFile(object):
    def __hash__(self):
        return hash("%s:%s" % (self.__class__.__name__, self.path()))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.path() == other.path()
        else:
            return False

    def hash(self, override=""):
        """Creates a cache buster value for the file"""
        return hashlib.md5(override + self.contents()).hexdigest()[:6]

    def path(self):
        """Gets the path of the file"""
        raise NotImplementError()

    def upload(self, contents, replace=False):
        """
        Uploads the file to its path with the given `content`, adding the
        appropriate parent directories when needed. If the path already exists
        and `replace` is `False`, the file will not be uploaded.
        """
        raise NotImplementError()

    def contents(self):
        """Gets the contents of the file"""
        raise NotImplementError()

    def exists(self):
        """Returns whether the path exists"""
        raise NotImplementError()

    def remove(self):
        """Removes the given file"""
        raise NotImplementError()

class LocalFile(CDNFile):
    """
    Specifies a file stored locally and hosted through Tornado's static asset
    engine
    """

    def __init__(self, static_path, file_path):
        self.static_path = static_path
        self.file_path = file_path
        self.full_path = os.path.join(self.static_path, self.file_path)

    def path(self):
        return self.file_path

    def upload(self, contents, replace=False):
        if replace or not os.path.exists(self.full_path):
            try:
                os.makedirs(os.path.dirname(self.full_path))
            except:
                pass

            with open(self.full_path, "wb") as f:
                f.write(contents)

    def contents(self):
        with open(self.full_path, "r") as f:
            return f.read()

    def exists(self):
        return os.path.exists(self.full_path)

    def remove(self):
        os.remove(self.full_path)

class S3File(CDNFile):
    """Specifies a file stored on Amazon S3"""

    def __init__(self, key):
        self.key = key

    def path(self):
        return self.key.name

    def upload(self, contents, replace=False):
        if replace or not self.key.exists():
            guessed_type = mimetypes.guess_type(self.path())[0]

            self.key.set_contents_from_string(contents, {
                "Content-Type": guessed_type or "binary/octet-stream",
                "Cache-Control": "'max-age=155520000, public'",
                "Expires": "'Sat, 29 Apr 2017 13:31:45-0000 GMT'"
            })

    def contents(self):
        return self.key.get_contents_as_string()

    def exists(self):
        return self.key.exists()

    def remove(self):
        self.key.delete()
