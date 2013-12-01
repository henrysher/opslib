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

import opslib
from boto.s3.connection import S3Connection
from opslib.icsexception import IcsS3Exception


class IcsS3(object):
    """
    ICS Library for S3
    """
    def __init__(self, **kwargs):
        self.conn = S3Connection(**kwargs)

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
            ## os.path.join will append "/" here
            ## should use '' not '/'
            ## os.path.join will take '/' as absolute path
            ## then the result: uri = '/'
            uri = os.path.join(uri, '')
        bucket_name, key_path = uri[len('s3://'):].split('/', 1)
        bucket = self.conn.get_bucket(bucket_name, validate=False)
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
            ## os.path.join will append "/" here
            ## should use '' not '/'
            ## os.path.join will take '/' as absolute path
            ## then the result: uri = '/'
            uri = os.path.join(uri, '')
        bucket_name, key_path = uri[len('s3://'):].split('/', 1)
        bucket = self.conn.get_bucket(bucket_name, validate=False)
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
        bucket = self.conn.get_bucket(bucket_name, validate=False)
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
        bucket = self.conn.get_bucket(bucket_name, validate=False)
        key = bucket.get_key(key_name)
        if key is None:
            raise IcsS3Exception('S3 file does not exist: "%s"' % (uri))
        return key.get_contents_as_string()

# vim: tabstop=4 shiftwidth=4 softtabstop=4
