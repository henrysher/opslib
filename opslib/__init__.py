"""
ICS Ops Common Library
"""

import os
from os.path import dirname
from os.path import realpath
from os.path import join as pathjoin

import boto

__version__ = "1.0.0"

CONFIG = "opslib.ini"
LOG_NAME = "opslib"
AWS_ACCESS_KEY_NAME = "aws_access_key_id"
AWS_SECRET_KEY_NAME = "aws_secret_access_key"


def init_boto_config(filepath=None):
    if filepath is None or not os.path.exists(filepath):
        pwdpath = dirname(realpath(__file__))
        filepath = pathjoin(pwdpath, CONFIG)

    from boto.pyami.config import Config
    boto.config = Config(filepath)

    access_key = boto.config.get('Credentials', AWS_ACCESS_KEY_NAME, None)
    secret_key = boto.config.get('Credentials', AWS_SECRET_KEY_NAME, None)
    if not access_key or not secret_key:
        boto.config.remove_section('Credentials')

    return access_key, secret_key


def init_botocore_config(filepath=None):
    if filepath is None or not os.path.exists(filepath):
        pwdpath = dirname(realpath(__file__))
        filepath = pathjoin(pwdpath, CONFIG)

    access_key, secret_key = init_boto_config(filepath)
    import botocore.credentials

    if access_key and secret_key:
        def get_credentials(session, metadata=None):
            return botocore.credentials.Credentials(access_key, secret_key)
        botocore.credentials.get_credentials = get_credentials


def init_logging(name=LOG_NAME, logfile=None,
                 console=0, loglevel="info",
                 enable_boto_log=False):
    global logger
    from icslog import IcsLog

    logger = IcsLog(name, console=console, logfile=logfile)
    func_name = "".join(["set_", loglevel.lower(), "_level"])
    getattr(logger, func_name)()

    if enable_boto_log:
        boto.log = logger
    return logger

init_boto_config()
init_logging()

# vim: tabstop=4 shiftwidth=4 softtabstop=4
