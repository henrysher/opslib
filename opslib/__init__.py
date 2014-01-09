"""
ICS Ops Common Library
"""

import os
from os.path import dirname
from os.path import realpath
from os.path import join as pathjoin

import boto

__version__ = "0.0.3"

CONFIG = "opslib.ini"
LOG_NAME = "opslib"
AWS_ACCESS_KEY_NAME = "aws_access_key_id"
AWS_SECRET_KEY_NAME = "aws_secret_access_key"


def init_config(filepath=None, enable_boto=True, enable_botocore=False):
    # Default credential file will be located at current folder
    if filepath is None or not os.path.exists(filepath):
        pwdpath = dirname(realpath(__file__))
        filepath = pathjoin(pwdpath, CONFIG)

    if enable_boto:
        # Initialize credentials for boto
        from boto.pyami.config import Config
        boto.config = Config(filepath)

        access_key = boto.config.get('Credentials', AWS_ACCESS_KEY_NAME, None)
        secret_key = boto.config.get('Credentials', AWS_SECRET_KEY_NAME, None)

        # FIXME: a trick when the value is empty
        if not access_key or not secret_key:
            boto.config.remove_section('Credentials')

    if enable_botocore:
        # Initialize credentials for botocore
        import botocore.credentials

        if access_key and secret_key:
            def get_credentials(session, metadata=None):
                return botocore.credentials.Credentials(access_key, secret_key)
            botocore.credentials.get_credentials = get_credentials

    if access_key and secret_key:
        return access_key, secret_key


def init_logging(name=LOG_NAME, logfile=None,
                 console=False, loglevel="INFO",
                 enable_boto_log=False):
    global logger
    from opslib.icslog import IcsLog
    logger = IcsLog(name, level=loglevel, console=console, logfile=logfile)

    if enable_boto_log:
        boto.log = logger
    return logger

init_config()
init_logging()

# vim: tabstop=4 shiftwidth=4 softtabstop=4
