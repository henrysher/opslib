"""
IcsS3: Library for S3
---------------------

+-------------------+------------+--+
| This is the IcsS3 common library. |
+-------------------+------------+--+
"""

import os
import re
import tempfile

from boto.s3.connection import S3Connection
from boto.s3.lifecycle import Lifecycle
from boto.exception import S3CreateError, S3ResponseError
from opslib.icsexception import IcsS3Exception

import logging
log = logging.getLogger(__name__)


class IcsS3(S3Connection):

    """
    ICS Library for S3
    """

    def __init__(self, **kwargs):
        super(IcsS3, self).__init__(**kwargs)

    def recursive_download(self, uri, pattern='', dirname=None):
        """
        Recursive download files from S3

        :type url: str
        :param url: File URL in S3, like ``s3://bucket/path``

        :type pattern: string
        :param pattern: regrex expression to match

        :type dirname: string
        :param dirname: local path to save, 'None' by default

        :rtype: list
        :return: a list containing dowloaded file path
        """
        if not uri.startswith("s3://"):
            raise IcsS3Exception('Invalid S3 URL: "%s"' % (uri))
        if not uri.endswith("/"):
            # os.path.join will append "/" here
            # should use '' not '/'
            # os.path.join will take '/' as absolute path
            # then the result: uri = '/'
            uri = os.path.join(uri, '')
        bucket_name, key_path = uri[len('s3://'):].split('/', 1)
        bucket = self.get_bucket(bucket_name, validate=False)
        keys = bucket.list(prefix=key_path)
        if dirname is None:
            tmpdir = tempfile.mkdtemp(prefix=bucket_name)
        else:
            tmpdir = tempfile.mkdtemp(prefix=dirname)

        localpath = []
        for key in keys:
            if re.compile(pattern).findall(key.name) != []:
                s3uri = "s3://" + os.path.join(bucket.name, key.name)
                fname = key.name.split('/')[-1]
                dirpath = os.path.join(tmpdir, fname)
                with open(dirpath, 'w') as f:
                    self.download_file(s3uri, f)
                localpath.append(dirpath)

        return localpath

    def batch_download(self, uri, pattern='', dirname=None):
        """
        Batch download files from S3 (only for current folder)

        :type url: str
        :param url: File URL in S3, like ``s3://bucket/path``

        :type pattern: string
        :param pattern: regrex expression to match

        :type dirname: string
        :param dirname: local path to save, 'None' by default

        :rtype: list
        :return: a list containing dowloaded file path
        """
        if not uri.startswith("s3://"):
            raise IcsS3Exception('Invalid S3 URL: "%s"' % (uri))
        if not uri.endswith("/"):
            # os.path.join will append "/" here
            # should use '' not '/'
            # os.path.join will take '/' as absolute path
            # then the result: uri = '/'
            uri = os.path.join(uri, '')
        bucket_name, key_path = uri[len('s3://'):].split('/', 1)
        bucket = self.get_bucket(bucket_name, validate=False)
        keys = bucket.list(prefix=key_path, delimiter="/")
        if dirname is None:
            tmpdir = tempfile.mkdtemp(prefix=bucket_name)
        else:
            tmpdir = tempfile.mkdtemp(prefix=dirname)

        localpath = []
        for key in keys:
            if re.compile(pattern).findall(key.name) != []:
                s3uri = "s3://" + os.path.join(bucket.name, key.name)
                fname = key.name.split('/')[-1]
                dirpath = os.path.join(tmpdir, fname)
                with open(dirpath, 'w') as f:
                    self.download_file(s3uri, f)
                localpath.append(dirpath)
        return localpath

    def download_file(self, uri, fp):
        """
        Download a file from S3

        :type url: str
        :param url: File URL in S3, like ``s3://bucket/path``

        :type fp: file
        :param fp: file descriptor from local file

        :rtype: string
        :return: a string containing dowloaded file name

        """
        if not uri.startswith("s3://"):
            raise IcsS3Exception('Invalid S3 URL: "%s"' % (uri))
        bucket_name, key_name = uri[len('s3://'):].split('/', 1)
        bucket = self.get_bucket(bucket_name, validate=False)
        key = bucket.get_key(key_name)
        if key is None:
            raise IcsS3Exception('S3 file does not exist: "%s"' % (uri))
        key.get_contents_to_file(fp)
        return fp.name

    def get_file_as_string(self, uri):
        """
        Get a file as string from S3

        :type url: str
        :param url: File URL in S3, like ``s3://bucket/path``

        :rtype: string
        :return: a string containing dowloaded file content

        """
        if not uri.startswith("s3://"):
            raise IcsS3Exception('Invalid S3 URL: "%s"' % (uri))
        bucket_name, key_name = uri[len('s3://'):].split('/', 1)
        bucket = self.get_bucket(bucket_name, validate=False)
        key = bucket.get_key(key_name)
        if key is None:
            raise IcsS3Exception('S3 file does not exist: "%s"' % (uri))
        return key.get_contents_as_string()

    def add_rule(self, id=None, prefix=None, status=None,
                 expiration=None, transition=None):
        """
        Add a rule to this Lifecycle configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this Lifecycle config object
        to the configure_lifecycle method of the Bucket object.

        :type id: str
        :param id: Unique identifier for the rule. The value cannot be longer
            than 255 characters.

        :type prefix: str
        :iparam prefix: Prefix identifying one or more objects to which the
            rule applies.

        :type status: str
        :param status: If 'Enabled', the rule is currently being applied.
            If 'Disabled', the rule is not currently being applied.

        :type expiration: int
        :param expiration: Indicates the lifetime, in days, of the objects
            that are subject to the rule. The value must be a non-zero
            positive integer. A Expiration object instance is also perfect.

        :type transition: Transition
        :param transition: Indicates when an object transitions to a
            different storage class.
        """
        self.lifecycle.add_rule(id, prefix, status, expiration, transition)

    def configure_s3rule(self, bucket, rules=None):
        """
        :type bucket: object
        :param bucket: the boto object of S3 bucket

        :type rules: dict
        :param rules: describes the lifecycle rules

        :rtype: list
        :return: a list of results
        """
        self.lifecycle = Lifecycle()
        if rules and isinstance(rules, dict):
            for id, rule in rules.iteritems():
                self.add_rule(id=id, **rule)
            try:
                old = bucket.get_lifecycle_config()
            except S3ResponseError, e:
                if "nosuchlifecycleconfiguration" in str(e).lower():
                    old = None
                else:
                    raise
            if old:
                log.info("old s3 rules found, need to delete first")
                bucket.delete_lifecycle_configuration()
                log.info("old s3 rules has been deleted: %s" % old)
            log.info("now add new s3 rules")
            return bucket.configure_lifecycle(self.lifecycle)
        else:
            raise IcsS3Exception("no lifecycle rule found...")

    def create_bucket(self, bucket_name, headers=None,
                      location="us-west-2", policy=None):
        """
        Creates a new located bucket. By default it's in the USA.

        :type bucket_name: string
        :param bucket_name: The name of the new bucket

        :type headers: dict
        :param headers: Additional headers to pass along with
            the request to AWS.

        :type location: str
        :param location: The location of the new bucket, like "us-west-2"

        :type policy: :class:`boto.s3.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied to the
            new key in S3.
        """
        if bucket_name and isinstance(bucket_name, basestring):
            try:
                return super(IcsS3, self).create_bucket(
                    bucket_name, headers, location, policy)
            except S3CreateError, e:
                if "bucketalreadyownedbyyou" in str(e).lower():
                    log.info(
                        "this bucket already exists, do the updating...")
                    return super(IcsS3, self).get_bucket(bucket_name)
                raise
        else:
            raise IcsS3Exception("no bucket name found...")

# vim: tabstop=4 shiftwidth=4 softtabstop=4
