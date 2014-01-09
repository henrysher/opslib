"""
Misc: Library for Misc
----------------------

+------------------------+---------+
| This is the Misc common library. |
+------------------------+---------+
"""

import os
import re
import json
import shlex
import base64
import random
import socket
from time import sleep, gmtime, strftime
from subprocess import Popen, PIPE, STDOUT
from types import GeneratorType as generator
from os.path import join as pathjoin
from copy import deepcopy

from boto.utils import retry_url
import botocore.session
from botocore import xform_name
from botocore.base import get_data as get_botocore_data

from opslib.icsutils.sshkey import PublicKey
from opslib.icsexception import IcsException
from opslib.icsexception import IcsSysCfgException

import logging
log = logging.getLogger(__name__)


class Retry(object):
    default_exceptions = (Exception)

    def __init__(self, tries, interval=0, exceptions=None):
        """Decorator for retrying function if exception occurs

        :type tries: int
        :param tries: how many times to retry your function

        :type exceptions: Exception
        :param exceptions: which exceptions you need to be
            caught to retry your function

        """
        self.tries = tries
        self.interval = interval
        if exceptions is None:
            exceptions = Retry.default_exceptions
        self.exceptions = exceptions

    def __call__(self, f):
        """
        retry calling your function
        """
        def fn(*args, **kwargs):
            exception = None
            for i in range(self.tries):
                # Use binary exponential backoff to desynchronize client
                # requests.
                if self.interval != 0:
                    next_sleep = self.interval
                else:
                    next_sleep = random.random() * (2 ** i)
                try:
                    return f(*args, **kwargs)
                except self.exceptions, e:
                    exception = e
                    # FIXME:
                    # logger.error(str(e))
                    if i + 1 != self.tries:
                        # FIXME:
                        # logger.info('Retrying in %3.1f seconds' % next_sleep)
                        sleep(next_sleep)

            # if no success after tries, raise last exception
            raise exception
        return fn


def exec_shell(cmd):
    """
    Execute Shell Commands

    (not support for pipe in shell command)

    :type cmd: string
    :param cmd: shell commands

    :rtype: tuple
    :return: a tuple containing (exitstatus, stdout, stderr)
    """
    if cmd is None or not isinstance(cmd, basestring):
        raise IcsException(
            "the command should be a 'str' not %s" % type(cmd))
    if isinstance(cmd, unicode):
        # prior to python v2.7.3, shlex does not support unicode
        # do not use "str" to avoid raw unicode
        cmd = cmd.encode("utf-8")
    pipe = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    stdout, stderr = pipe.communicate()
    status = pipe.returncode
    return (status, stdout, stderr)


def exec_shell_pipe(cmd):
    """
    Execute Shell Commands

    :type cmd: string
    :param cmd: shell commands

    :rtype: string or bool
    :return: False or error reason
    """
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    (stdoutdata, stderrdata) = p.communicate()
    status = p.returncode
    return (status, stdoutdata)


def get_userdata(version='latest',
                 url='http://169.254.169.254',
                 timeout=None, num_retries=5):
    """
    Returns the instance userdata as a string by default.

    If the timeout is specified, the connection to the specified url
    will time out after the specified number of seconds.

    :type version: str
    :param version: API version from AWS

    :type timeout: int
    :param timeout: socket timeout

    :type num_retries: int
    :param num_retries: how many times of retrying

    :rtype: string
    :return: a string containing user data

    """
    if timeout is not None:
        original = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
    ud_url = '%s/%s/%s/' % (url, version, 'user-data')
    user_data = retry_url(
        ud_url, retry_on_404=False, num_retries=num_retries)
    if timeout is not None:
        socket.setdefaulttimeout(original)
    return user_data


class IcsSysCfg(object):

    """
    ICS Library for System Configuration
    """

    def __init__(self):
        # FIXME: avoid to cause exceptions when generating documents
        import opslib.icsutils.augeas as augeas
        self.aug = augeas.Augeas()

    def __del__(self):
        self.aug.close()

    def update_sshpub(self, user="ics-user", sshpub=None):
        """
        Update SSH Public Key

        :type user: string
        :param user: to determine which user to update

        :type sshpub: string
        :param sshpub: SSH public key contents
        """
        if user == "root":
            fname = "/root/.ssh/authorized_keys"
        else:
            fname = "/home/%s/.ssh/authorized_keys" % user

        new_pub, new_keys = self.parse_sshpub(sshpub)
        if os.path.exists(fname):
            with open(fname, "r") as f:
                ftext = f.read()
            old_pub, old_keys = self.parse_sshpub(ftext)

            new_text = ""
            for new_key in new_keys:
                if new_key not in old_keys:
                    new_text += new_pub[new_key].text
        else:
            new_text = ""
            for new_key in new_keys:
                new_text += new_pub[new_key].text
        with open(fname, "a") as f:
            f.write(new_text)

    def parse_sshpub(self, sshpub=None):
        """
        Parse SSH Public Key

        :type sshpub: string
        :param sshpub: SSH public key contents
        """
        if sshpub is None:
            raise IcsSysCfgException("public SSH key is %s" % type(sshpub))
        keys = []
        elements = {}
        for line in sshpub.split("\n"):
            if line and not line.startswith("#"):
                key = PublicKey(line.strip())
                keys.append(key.blob)
                elements.update({key.blob: key})

        return elements, keys

    def update_host_name(self, hostname):
        """
        Update hostname

        :type hostname: string
        :param hostname: hostname need to udpate
        """
        fname = "/files/etc/sysconfig/network"
        ret_hosts = self.to_dict(self.recurmatch(fname))
        if ret_hosts == {}:
            raise IcsSysCfgException(
                "cannot correctly parse the config file '%s'" % fname)
        path = os.path.join(fname, 'HOSTNAME')
        self.update_cfg(path, hostname)

    def update_hosts_file(self, ipaddr, hostname):
        """
        Update /etc/hosts with (ipaddr, hostname) pair

        :type ipaddr: string
        :param ipaddr: IP address

        :type hostname: string
        :param hostname: hostname
        """
        fname = "/files/etc/hosts"
        ret_hosts = self.to_dict(self.recurmatch(fname))
        if ret_hosts == {}:
            raise IcsSysCfgException(
                "cannot correctly parse the config file '%s'" % fname)

        flag = 0
        for host in ret_hosts:
            ret_host = ret_hosts[host]
            if ret_host['ipaddr'] == ipaddr:
                flag += 1
                if hostname in ret_host.values():
                    # FIXME:
                    # logger.info("the hostname '%s' already exists in '%s'" %
                    #             (hostname, fname))
                    continue
                count = 0
                for hostkey in ret_host.keys():
                    if 'alias' in hostkey:
                        count += 1
                path = os.path.join(host, 'alias[%s]' % str(count + 1))
                self.update_cfg(path, hostname)

        if flag == 0:
            # FIXME:
            # logger.info("the ipaddr '%s' does not exist in '%s'" % (
            #     ipaddr, fname))
            prefix = os.path.join(fname, str(len(ret_hosts) + 1))
            path = os.path.join(prefix, 'ipaddr')
            self.update_cfg(path, ipaddr)
            path = os.path.join(prefix, 'canonical')
            self.update_cfg(path, hostname)

    def update_cfg(self, path, value):
        """
        Update configuration via augeas library (low-level)

        :type path: string
        :param path: augeas path

        :type value: string
        :param value: value
        """
        self.aug.set(path, value)
        self.aug.save()
        self.aug.load()
        if self.aug.get(path) != value:
            raise IcsSysCfgException(
                "cannot update '%s' for '%s'" % (path, value))
        # logger.info("'%s' updated as '%s'" % (path, value))

    def to_dict(self, data):
        """
        Convert augeas output as dict format (low-level)

        :type data: generator
        :param data: augeas output data

        :rtype: dict
        :return: a dictionary contains augeas output data
        """
        if isinstance(data, generator):
            ret = {}
            for (k, v) in data:
                fir, sec = tuple(k.rsplit("/", 1))
                if fir in ret:
                    ret[fir].update({sec: v})
                else:
                    ret[fir] = {sec: v}
            return ret
        else:
            msg = "invalid input type:" +\
                  "should be a <type 'generator'>," +\
                  "but not %s" % type(data)
            raise IcsSysCfgException(msg)

    def recurmatch(self, path):
        """
        Get augeas output via recursive solution (low-level)

        :type path: string
        :param path: augeas string
        """
        if path:
            if path != "/":
                val = self.aug.get(path)
                if val:
                    yield (path, val)

        m = []
        if path != "/":
            self.aug.match(path)
        for i in m:
            for x in self.recurmatch(i):
                yield x
        else:
            for i in self.aug.match(path + "/*"):
                for x in self.recurmatch(i):
                    yield x


def dict_merge(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


def traverse_json(data, delimiter="/", path="", output=None):
    """
    Traverse all the items in JSON data

    :type data: dict, list, element
    :param data: JSON data

    :type delimiter: string
    :param delimiter: path delimiter for each JSON node

    :type path: string
    :param path: record the parent path on this JSON data

    :type output: dict
    :param output: record each item with full path
    """
    if output is None:
        output = {}
    if not data:
        return output
    elif isinstance(data, dict):
        for element in data:
            new_path = delimiter.join([path, str(element)])
            output = traverse_json(data[element], path=new_path, output=output)
    elif isinstance(data, list):
        for element in data:
            new_path = delimiter.join([path, str(data.index(element))])
            output = traverse_json(element, path=new_path, output=output)
    elif path:
        output[path] = data
    return output


def filter_resource_from_json(names=None, filter=None, raw_data=None):
    """
    Filter the resource with specified filter on JSON data

    :type names: list
    :param names: specify the list of resoure names to filter
        Ex: ["AutoScalingGroupName", "LaunchConfigurationName"]

    :type filter: dict
    :param filter: describe the filter in details

    :type raw_data: dict
    :param raw_data: resource data in JSON format

    :rtype: list
    :return: a list containing all the names for filtered resources
    """
    if names is None:
        names = []
    if filter is None:
        filter = {}
    if raw_data is None:
        raw_data = {}

    data = {}
    for item in raw_data[raw_data.keys()[0]]:
        t = tuple([item.get(name, None) for name in names])
        data[t] = traverse_json(item)

    finder = traverse_json(filter)

    resources = []
    pattern = "\/\d\/"
    sample = "/index/"
    for k1, v1 in data.iteritems():
        for k2, v2 in finder.iteritems():
            flag = False
            for k3, v3 in v1.iteritems():
                k_1 = re.sub(pattern, sample, k2)
                k_2 = re.sub(pattern, sample, k3)
                if k_1 == k_2 and v2 == v3:
                    flag = True
                    break
            if not flag:
                break
        else:
            resources.append(k1)
    return resources


def init_botocore_service(name, region):
    """
    Initialize the proper service with botocore
    """
    session = botocore.session.get_session()
    service = session.get_service(name)
    endpoint = service.get_endpoint(region)
    return service, endpoint


def check_error(response_data):
    """
    A helper function that prints out the error message recieved in the
    response_data and raises an error when there is an error.
    """
    if response_data:
        if 'Errors' in response_data:
            errors = response_data['Errors']
            for error in errors:
                raise IcsException("Error: %s\n" % error)


def operate(service, cmd, kwargs):
    """
    A helper function that universally calls any command by taking in the
    service, name of the command, and any additional parameters required in
    the call.
    """
    operation = service.get_operation(cmd)
    http_response, response_data = operation.call(**kwargs)
    check_error(response_data)
    return http_response, response_data


def drop_null_items(obj):
    for key in obj.keys():
        # For "if" statement,
        # Here are some scenarios for the condition to be true:
        #
        # 1. None
        # 2. False
        # 3. zero for numeric types
        # 4. empty sequences
        # 5. empty dictionaries
        # 6. a value of 0 or False returned
        #    when either __len__ or __nonzero__ is called
        #
        # In this fuction, we need to consider these as null items:
        # 1. None; 4. empty sequences; 5. empty dictionaries

        if isinstance(obj[key], bool) or isinstance(obj[key], int):
            continue
        elif not obj[key]:
            del obj[key]
    return obj


def convert_keyname(obj):
    for key in obj.keys():
        new_key = xform_name(key)
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj


def keyname_format(fp_json):
    """
    Convert the key name of JSON data: from camel case to a "pythonic" name.

    :type fp_json: object
    :param fp_json: opened file object
    """
    return convert_keyname(json.load(fp_json, object_hook=drop_null_items))


def keyname_formats(str_json):
    """
    Convert the key name of JSON data: from camel case to a "pythonic" name.

    :type str_json: string
    :param str_json: JSON data
    """
    return convert_keyname(json.loads(str_json, object_hook=drop_null_items))


def keyname_formatd(dict_json):
    """
    Convert the key name of JSON data: from camel case to a "pythonic" name.

    :type dict_json: dict
    :param dict_json: JSON data
    """
    return convert_keyname(json.loads(json.dumps(dict_json),
                           object_hook=drop_null_items))


def clean_empty_items(dict_json):
    """
    Clean Empty Items in the Dictionary: None, {}, [], ""
    """
    return json.loads(json.dumps(dict_json), object_hook=drop_null_items)


def get_search_path(search_paths):
    """
    Return the complete folder path used when searching for
    data files.

    :type search_paths: list
    :param search_paths: a list of folder paths to search
    """
    if isinstance(search_paths, list):
        paths = []
        for path in search_paths:
            path = os.path.expandvars(path)
            path = os.path.expanduser(path)
            paths.append(path)
        return paths
    else:
        return None


def get_data(search_path):
    """
    Get the complete data paths under the path to search

    :type search_path: string
    :param search_path: describes the folder path to search
    """
    if os.path.isfile(search_path):
        return [search_path]
    else:
        return [pathjoin(search_path, f) for f in os.listdir(search_path)
                if os.path.isfile(pathjoin(search_path, f))]


def get_search_files(search_paths):
    """
    Get the complete data paths under all the folder paths to search

    :type search_paths: list
    :param search_paths: a list of folder paths to search
    """
    if isinstance(search_paths, list):
        search_files = {}
        search_files.update({path: get_data(
            path) for path in get_search_path(search_paths)})
        return search_files
    else:
        return None


def get_search_file(name, search_paths):
    """
    Get the complete data path matched with the specified name

    :type name: string
    :param name: specified name need to match

    :type search_paths: list
    :param search_paths: a list of folder paths to search
    """
    if isinstance(search_paths, list):
        search_files = {}
        for path in get_search_path(search_paths):
            search_files.update({path: filepath for filepath in get_data(
                path) if name in filepath})
        return search_files
    else:
        return None


def is_valid_ip(ip_address):
    """
    Check Validity of an IP address
    """
    valid = True
    try:
        socket.inet_aton(ip_address.strip())
    except Exception:
        valid = False
    return valid


def format_aws_tags(resource_id, tags):
    """
    Refine the format of tags under AWS tag syntax

    :type resource_id: string
    :param resource_id: AWS Resource Id

    :type tags: list
    :param tags: a list of tags to refine
    """
    api_tags = []
    for key, value in tags.iteritems():
        new_tag = {}
        if isinstance(key, list):
            new_tag['Key'] = ",".join(key)
        elif key is None:
            continue
        else:
            new_tag['Key'] = key
        if isinstance(value, list):
            new_tag['Value'] = ",".join(value)
        elif value is None:
            continue
        else:
            new_tag['Value'] = value
        new_tag['PropagateAtLaunch'] = True
        new_tag['ResourceId'] = resource_id
        api_tags.append(new_tag)
    return api_tags


def fetch_used_params(service_name, cmd_name, params):
    """
    Fetch used parameters from the whole configuration
    """
    if not isinstance(params, dict):
        return None
    path = '/'.join(['aws', service_name, 'operations',
                    cmd_name, 'input', 'members'])
    session = botocore.session.get_session()
    required_params = get_botocore_data(session, path)
    used_params = {}
    for key, value in params.iteritems():
        if key in required_params:
            used_params.update({key: value})
    return keyname_formatd(used_params)


def gen_timestamp(format="%Y%m%d-%H%M%S"):
    return strftime(format, gmtime())


def user_data_decode(user_data):
    return base64.b64decode(user_data)


# vim: tabstop=4 shiftwidth=4 softtabstop=4
