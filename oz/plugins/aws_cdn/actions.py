from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

# Module for generating hashes for files that match a glob, and putting that
# hash in redis to allow us to generate cache-busting URLs later

import os
import oz
import oz.app
import oz.plugins.redis
import oz.plugins.aws_cdn

@oz.action
def cache_busting_scan(*prefixes):
    """
    (Re-)generates the cache buster values for all files with the specified
    prefixes.
    """

    settings = oz.app.settings
    redis = oz.plugins.redis.create_connection()

    # Get all items that match any of the patterns. Put it in a set to
    # prevent duplicates.
    if settings["s3_bucket"]:
        bucket = oz.plugins.aws_cdn.get_bucket()
        matches = set([oz.plugins.aws_cdn.S3File(key) for prefix in prefixes for key in bucket.list(prefix)])
    else:
        matches = set([])
        static_path = settings["static_path"]
        
        for root, _, filenames in os.walk(static_path):
            for filename in filenames:
                path = os.path.relpath(os.path.join(root, filename), static_path)

                for prefix in prefixes:
                    if path.startswith(prefix):
                        matches.add(oz.plugins.aws_cdn.LocalFile(static_path, path))
                        break

    # Set the cache busters
    for f in matches:
        file_hash = f.hash(override=settings.get("hash_override", ""))
        print(file_hash, f.path())
        oz.plugins.aws_cdn.set_cache_buster(redis, f.path(), file_hash)
