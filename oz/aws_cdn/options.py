"""Options for the aws_cdn plugin"""

from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

import oz

oz.options(
    aws_access_key = dict(type=str, default=None, help="AWS access key for CDN"),
    aws_secret_key = dict(type=str, default=None, help="AWS secret key for CDN"),
    static_host = dict(type=str, help="CDN hostname for static assets"),
    s3_bucket = dict(type=str, default=None, help="S3 bucket for uploading CDN assets"),
    s3_prefix = dict(type=str, default="", help="S3 key prefix to apply when operating on CDN assets"),
    s3_host = dict(type=str, default=None, help="S3 host to use for signature generation")
)
