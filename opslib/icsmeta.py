"""
IcsMeta: Library for Meta
--------------------------

+---------------------+------------+--+
| This is the IcsMeta common library. |
+---------------------+------------+--+
"""

import os
import re
import json
import time

from boto import config
from boto.utils import get_instance_metadata as get_metadata
from opslib.icss3 import IcsS3
from opslib.icsec2 import IcsEc2
from opslib.icsutils.misc import get_userdata
from opslib.icsutils.misc import is_valid_ip
from opslib.icsutils.icsalert import IcsAlert
from opslib.icsexception import IcsMetaException

import logging
log = logging.getLogger(__name__)


class IcsMeta(object):

    def __init__(self):
        """
        Initialize Ics Meta (meta-data, user-data, credentials, tags)
        """
        self.meta_data = IcsMeta.get_meta_data()
        self.user_data = json.loads(IcsMeta.get_user_data())
        self.credentials = self.get_credentials()
        self.tags = self.get_machine_tags()

    @staticmethod
    def get_meta_data(timeout=None, url=None, num_retries=None):
        """
        Get instance meta data

        :type timeout: int
        :param timeout: timeout for the request

        :type url: string
        :param url: metadata_service_url

        :type num_retries: int
        :param num_retries: how many times to retry

        :rtype: dict
        :return: instance meta data as a dictionary
        """
        if timeout is None:
            timeout = config.getint('Boto', 'http_socket_timeout', 70)
        if num_retries is None:
            num_retries = config.getint('Boto', 'num_retries', 5)
        if url is None:
            url = config.get(
                'Boto', 'metadata_service_url', 'http://169.254.169.254')
        return get_metadata(timeout=timeout, url=url, num_retries=num_retries)

    @staticmethod
    def get_user_data(timeout=None, url=None, num_retries=None):
        """
        Get instance user data

        :type timeout: int
        :param timeout: timeout for the request

        :type url: string
        :param url: metadata_service_url

        :type num_retries: int
        :param num_retries: how many times to retry

        :rtype: dict
        :return: instance user data as a dictionary
        """
        if timeout is None:
            timeout = config.getint('Boto', 'http_socket_timeout', 70)
        if num_retries is None:
            num_retries = config.getint('Boto', 'num_retries', 5)
        if url is None:
            url = config.get(
                'Boto', 'metadata_service_url', 'http://169.254.169.254')
        return get_userdata(timeout=timeout, url=url, num_retries=num_retries)

    def get_credentials(self):
        """
        Get AWS credentials from instance user-data

        :rtype: dict
        :return: AWS credentials as a dictionary
        """
        try:
            access_key = self.user_data[
                'Credentials']['AWS_ACCESS_KEY_ID']
            secret_key = self.user_data[
                'Credentials']['AWS_SECRET_ACCESS_KEY']
            credentials = {'aws_access_key_id': access_key,
                           'aws_secret_access_key': secret_key}
            return credentials
        except KeyError:
            return None

    def get_region(self):
        """
        Get the region from instance meta-data

        :rtype: string
        :return: the region name
        """
        try:
            return self.meta_data['placement'][
                'availability-zone'][:-1].strip()
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'region info' in meta-data.")

    def get_zone(self):
        """
        Get the availability zone from instance meta-data

        :rtype: string
        :return: the availability zone name
        """
        try:
            return self.meta_data['placement'][
                'availability-zone'][-1].strip()
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'availability zone' in meta-data.")

    def get_public_ip(self):
        """
        Get the public ip address from instance meta-data

        :rtype: string
        :return: the public ip address
        """
        try:
            self.meta_data = IcsMeta.get_meta_data()
            return self.meta_data["public-ipv4"]
        except KeyError:
            return None
        #    raise IcsMetaException(
        #        "Cannot find the 'public ip address' in meta-data.")

    def get_private_ip(self):
        """
        Get the private ip address from instance meta-data

        :rtype: string
        :return: the private ip address
        """
        try:
            self.meta_data = IcsMeta.get_meta_data()
            return self.meta_data["local-ipv4"]
        except KeyError:
            return None

    def get_public_hostname(self):
        """
        Get the public hostname from instance meta-data

        :rtype: string
        :return: the public hostname
        """
        try:
            self.meta_data = IcsMeta.get_meta_data()
            return self.meta_data["public-hostname"]
        except KeyError:
            raise IcsMetaException(
                'Cannot find the public hostname in meta-data.')

    def get_sns_topic(self):
        """
        Get the SNS Topic from instance user-data

        :rtype: string
        :return: the SNS Topic name
        """
        try:
            sns_topic = self.user_data['Bootstrap']['SNS_Topic']
            return sns_topic
        except KeyError:
            raise IcsMetaException("Cannot find the 'SNS topic' in user-data.")

    def get_cfg_bucket(self):
        """
        Get the Config Bucket from instance user-data

        :rtype: string
        :return: the Config Bucket name
        """
        try:
            cfg_bucket = self.user_data['S3']['ConfigBucket']
            return cfg_bucket
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'Config Bucket' in user-data.")

    def get_script_url(self):
        """
        Get the S3 url for import scripts from instance user-data

        :rtype: string
        :return: the s3 url for scripts
        """
        try:
            script_url = self.user_data['Bootstrap']['URL']
            return script_url
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'URL' in user-data.")

    def get_instance_id(self):
        """
        Get the instance id from instance meta-data

        :rtype: string
        :return: the instance id
        """
        try:
            return self.meta_data["instance-id"]
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'instance id' in meta-data.")

    def get_openssh_pubkey(self):
        """
        Get the openssh public key from instance meta-data

        :rtype: string
        :return: the contents of openssh public key
        """
        try:
            return self.meta_data['public-keys'].values()[0][0]
        except KeyError:
            raise IcsMetaException(
                "Cannot find the 'openssh-key' in meta-data.")

    def get_machine_tags(self, timeout=120):
        """
        Get the instance tags

        :rtype: string
        :return: the tags of this instance
        """
        region = self.get_region()
        instance_id = self.get_instance_id()

        if self.credentials is None:
            ec2conn = IcsEc2(region)
        else:
            ec2conn = IcsEc2(region, **self.credentials)

        for i in xrange(timeout / 5):
            result = ec2conn.get_instance_tags(instance_id)
            if result:
                return result
            time.sleep(5)
        else:
            # To avoid specific tags with "TypeError" Exception
            return {}

    def get_eips_from_tag(self):
        """
        Get the EIP list from instance tags

        :rtype: list
        :return: the list contains EIP addresses
        """
        try:
            eiplist = self.tags['EIPList']
        except KeyError:
            return None

        if eiplist is None:
            return None
        elif not isinstance(eiplist, basestring):
            return None

        if eiplist.startswith("s3://"):
            if self.credentials is None:
                s3conn = IcsS3()
            else:
                s3conn = IcsS3(**self.credentials)

            data = s3conn.get_file_as_string(eiplist)
            return re.split('[ \t\n,;]+', data.strip())
        else:
            eips = re.split('[ \t\n,;]+', eiplist.strip())
            results = []
            for eip in eips:
                if is_valid_ip(eip):
                    results.append(eip)
            if not results:
                return None
            else:
                return results

    def get_dns_from_tag(self):
        """
        Get the DnsName from instance tags

        :rtype: string
        :return: the DnsName
        """
        try:
            return self.tags['DnsName']
        except KeyError:
            return None

    def get_role_name(self):
        """
        Get the Role name from instance tags

        :rtype: string
        :return: the Role name
        """
        try:
            return self.tags['Role']
        except KeyError:
            return None

    def get_instance_name(self):
        """
        Get the Instance name from instance tags

        :rtype: string
        :return: the Instance name
        """
        try:
            # Ensure the same case as the name of subfolder for S3
            # configuration
            return self.tags['Name'].lower()
        # To avoid SNS Alert being not initialized
        except Exception:
            return None

    def generate_hostname(self):
        """
        Generate the hostname

        :rtype: string
        :return: the hostname
        """
        try:
            return '-'.join([self.get_instance_name(),
                             self.get_zone(),
                             self.get_instance_id()[2:]
                             ])
        except KeyError:
            raise IcsMetaException(
                "Failed to generate instance hostname.")

    def is_eip_ready(self, eip):
        """
        check the readiness of the specified EIP address

        :type eip: string
        :param eip: one EIP address

        :rtype: boolean
        :return: True/False
        """
        if eip != self.get_public_ip():
            return False
        return True

    def download_script(self, pattern):
        """
        Download scripts from S3

        :type pattern: string
        :param pattern: regrex expression to match

        :rtype: string
        :return: the local path where downloaded files stored
        """
        if self.credentials is None:
            s3conn = IcsS3()
        else:
            s3conn = IcsS3(**self.credentials)
        script_uri = self.get_script_url()
        localpath = s3conn.batch_download(script_uri, pattern=pattern)
        return localpath

    def download_cfg(self, pattern):
        """
        Download configuration files from S3

        :type pattern: string
        :param pattern: regrex expression to match

        :rtype: string
        :return: the local path where downloaded files stored
        """
        if self.credentials is None:
            s3conn = IcsS3()
        else:
            s3conn = IcsS3(**self.credentials)
        rolecfg_uri = "s3://" + os.path.join(self.get_cfg_bucket(),
                                             self.get_role_name())
        localpath = s3conn.batch_download(rolecfg_uri, pattern=pattern)
        instcfg_uri = os.path.join(rolecfg_uri, self.get_instance_name())
        localpath.extend(s3conn.batch_download(instcfg_uri, pattern=pattern))
        return localpath

    def init_config(self):
        """
        Combine meta-data, user-data, tags into one json string

        :rtype: dict
        :return: json string contains meta-data, user-data, tags
        """
        data = {}
        data.update({'MetaData': self.meta_data})
        data.update({'UserData': self.user_data})
        data.update({'Tags': self.get_machine_tags()})
        return data

    def init_alert(self, prefix='ICS'):
        """
        Intialize ICS Alert

        :type prefix: str
        :param prefix: prefix string to indicate which process

        :rtype: class
        :return: the instance of initialized IcsAlert class
        """
        sns_region = self.get_region()
        sns_topic = self.get_sns_topic()
        instance_id = self.get_instance_id()
        instance_name = self.get_instance_name()
        if instance_name is None:
            msg_prefix = "%s|%s|%s" % (prefix, sns_region,
                                       instance_id)
        else:
            msg_prefix = "%s|%s|%s|%s" % (prefix, sns_region,
                                          instance_name,
                                          instance_id)
        if self.credentials is None:
            alert = IcsAlert(sns_region, sns_topic, msg_prefix)
        else:
            alert = IcsAlert(
                sns_region, sns_topic, msg_prefix, **self.credentials)
        log.info("Alert setup in SNS topic '%s' with the prefix '%s'" %
                (sns_topic, msg_prefix))
        return alert

# vim: tabstop=4 shiftwidth=4 softtabstop=4
