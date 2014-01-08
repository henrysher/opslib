"""
JsonSubs: Library for JSON Template Substitutions
-------------------------------------------------

+------------------------+-------------+
| This is the JsonSubs common library. |
+------------------------+-------------+
"""

import re
import base64
import traceback

from opslib.icsutils.misc import dict_merge
from opslib.icsexception import IcsException

import logging
log = logging.getLogger(__name__)

import jmespath

try:
    import simplejson as json
except ImportError:
    import json


class DefaultFunc(object):

    """
    Default Functions for JsonSubs Library
    """

    @staticmethod
    def func_join(delimiter, params):
        """
        Builtin Func: Join

        .. code-block:: javascript

            {
                "$<Join>": ["-", ["a", "b", "c"] ]
            }
        """
        if isinstance(params, list):
            for value in params:
                if not isinstance(value, basestring):
                    break
            else:
                return delimiter.join(params)

        raise IcsException("Invalid parameters found: (%s,%s)" % (
            delimiter, params))

    @staticmethod
    def func_include(*args):
        """
        Builtin Func: Include

        .. code-block:: javascript

            {
                "$<Include>": [ "a.json", "b.json" ]
            }
        """
        if isinstance(args, basestring):
            return JsonSub.fp_to_json(open(args, "r"))

        elif isinstance(args, tuple):
            text = {}
            for value in args:
                if not isinstance(value, basestring):
                    break
                log.debug("Including the config file: %s" % value)
                text = dict_merge(text, json.load(open(value, "r")))
            else:
                return text

        raise IcsException("Invalid parameters found: (%s)" % (
            args))

    @staticmethod
    def func_base64(params):
        """
        Builtin Func: Base64

        .. code-block:: javascript

            {
                "$<Base64>": "xxxxxxxx"
            }
        """
        if isinstance(params, basestring):
            import base64
            return base64.b64encode(params)

        raise IcsException("Invalid parameters found: %s" % params)

    @staticmethod
    def func_select(index, params):
        """
        Builtin Func: Select

        .. code-block:: javascript

            {
                "$<Select>": [ 1, [ "apples", "grapes", "mangoes" ] ]
            }
        """
        if isinstance(params, list):
            if isinstance(index, int):
                # The first number would be 1
                return params[index - 1]
            elif isinstance(index, basestring):
                # The first number would be "1"
                return params[int(index) - 1]

        raise IcsException(
            "Invalid parameters found: (%s,%s)" % (index, params))

    @staticmethod
    def func_circle_select(index, params):
        """
        Builtin Func: CSelect

        .. code-block:: javascript

            {
                "$<CSelect>": [ 5, [ "apples", "grapes", "mangoes" ] ]
            }
        """
        if isinstance(params, list):
            if isinstance(index, int):
                # The first number would be 1
                return params[(index - 1) % len(params)]
            elif isinstance(index, basestring):
                # The first number would be "1"
                return params[(int(index) - 1) % len(params)]

        raise IcsException(
            "Invalid parameters found: (%s,%s)" % (index, params))


class JsonSubs(object):

    def __init__(self):
        """
        JSON Template Substitution Library

        **Detail Examples:**

        >>> from opslib.icsutils.jsonsubs import JsonSubs
        >>> engine = JsonSubs()
        >>> test_data = ["-", ["a", "b", "c"]]
        >>> print engine.builtin["Join"](test_data)
        a-b-c

        >>> import opslib
        >>> from opslib.icsutils.jsonsubs import JsonSubs
        >>> engine = JsonSubs()
        >>> from opslib.icsec2 import IcsEc2
        >>> ec2 = IcsEc2("us-west-2")
        >>> func = ec2.conn.get_all_instances
        >>> engine.register_builtin({"GetAllInstances": func})
        >>> print engine.builtin["GetAllInstances"]()
        [ Reservation:r-be459c8c,
          Reservation:r-e6822ed4,
          Reservation:r-e66dc3d4,
          Reservation:r-1608a124,
          Reservation:r-ce0da4fc ]

        >>> import opslib
        >>> from opslib.icsutils.jsonsubs import JsonSubs
        >>> engine = JsonSubs()
        >>> from opslib.icsec2 import IcsEc2
        >>> ec2 = IcsEc2("us-west-2")
        >>> func = ec2.get_instance_tags
        >>> engine.register_builtin({"GetInstanceTags": func})
        >>> default_json = {
        ...     "version": "1.2.0",
        ...     "Ids": [ "25d6d811", "12345678" ],
        ...     "RegionMaps": {
        ...         "us-east-1": { "32": "ami-xx", "64": "ami-yy" },
        ...         "us-west-2": { "32": "ami-xy", "64": "ami-yx" }
        ...     }
        ... }
        >>> output_json = {
        ...     "Version": "$(version)",
        ...     "Id": { "$<Select>": [0, "$[Ids]"] },
        ...     "UserData": { "$<Base64>": "$(Id)" },
        ...     "Maps": "${RegionMaps}",
        ...     "InstanceId": { "$<Join>": [ "-", [ "i", "$(Id)" ] ] },
        ...     "Tags": { "$<GetInstanceTags>": "$(InstanceId)" }
        ... }
        >>> instance_json = output_json
        >>> print engine.tplsub(output_json, instance_json, default_json)
        {
            "Id": "25d6d811",
            "InstanceId": "i-25d6d811",
            "Maps": {
                "us-east-1": {
                    "32": "ami-xx",
                    "64": "ami-yy"
                },
                "us-west-2": {
                    "32": "ami-xy",
                    "64": "ami-yx"
                }
            },
            "Tags": "ec2-50-112-231-217.us-west-2.compute.amazonaws.com",
            "UserData": "MjVkNmQ4MTE=",
            "Version": "1.2.0"
        }

        **Notes:**
           * Do NOT define ``Variables`` in `output_json`, \
             otherwise, please merge `output_json` into `instance_json` \
             or `default_json`
           * ``Variables`` should be defined in `instance_json`\
             or `default_json`
           * If no such `instance_json` and `default_json`, \
             take `output_json` also as `instance_json`
           * If no such ``Variables`` found in `instance_json`, \
             use one in `default_json`

        """
        self.default_builtin = {
            "Join": DefaultFunc.func_join,
            "Base64": DefaultFunc.func_base64,
            "Select": DefaultFunc.func_select,
            "CSelect": DefaultFunc.func_circle_select,
            "Include": DefaultFunc.func_include,
            "Mapping": self.func_mapping,
        }
        self.builtin = self.default_builtin
        self.instance_vars = None
        self.default_vars = None

    def func_mapping(self, map_name, *args):
        """
        Builtin Func: Mapping

        .. code-block:: javascript

            {
                "$<Mapping>": [ "MapName", "TopLevelKey", ... ]
            }
        """
        if isinstance(map_name, basestring) and \
                (not args or isinstance(args, tuple)):
            if map_name in self.default_vars:
                tmp = self.default_vars
            elif map_name in self.instance_vars:
                tmp = self.instance_vars
            else:
                return None

            try:
                tmp0 = tmp[map_name]
                return reduce(lambda x, y: x[y], args, tmp0)

            except Exception:
                msg = traceback.format_exc()
                raise IcsException(
                    "Error found in <Mapping>: %s \n %s" % (map_name, msg))

        raise IcsException(
            "Invalid parameters found: (%s,%s)" % (map_name, args))

    def register_builtin(self, customized_func):
        """
        Register Customized Functions

        :type customized_func: dict
        :param customized_func: describes customized functions to register

        .. code-block:: javascript

            {
               "Join": DefaultFunc.func_join,
               "FindAMI": DefaultFunc.func_find_ami,
               "GetInstanceTags": IcsEc2.get_instance_tags
            }
        """
        self.builtin.update(customized_func)

    def merge_map(self, key, instance_vars=None, default_vars=None):
        if self.type_of(key)[0] is None:
            path = jmespath.compile(key)
            if path.search(instance_vars):
                return path.search(instance_vars)
            elif path.search(default_vars):
                return path.search(default_vars)
            else:
                return None
        else:
            return self.merge_map(self.tplsub(key, instance_vars,
                                              default_vars),
                                  instance_vars, default_vars)

    def merge_str(self, key, instance_vars=None, default_vars=None):
        if key in instance_vars:
            return instance_vars[key]
        elif key in default_vars:
            return default_vars[key]
        else:
            return None

    def merge_dict(self, key, instance_vars=None, default_vars=None):
        ret = {}
        if key in instance_vars:
            if self.type_of(instance_vars[key])[0] is None:
                ret.update(instance_vars[key])
        if key in default_vars:
            if self.type_of(default_vars[key])[0] is None:
                ret.update(default_vars[key])
        return ret

    def merge_list(self, key, instance_vars=None, default_vars=None):
        ret = []
        if key in instance_vars:
            if self.type_of(instance_vars[key])[0] is None:
                ret.extend(instance_vars[key])
        if key in default_vars:
            if self.type_of(default_vars[key])[0] is None:
                ret.extend(default_vars[key])
        return ret

    def do_sub(self, value, instance_vars=None, default_vars=None):
        """
        Execute JSON Template Substitutions
        """
        do_type, key = self.type_of(value)
        if do_type is None:
            return value
        elif do_type == "str":
            return self.merge_str(key, instance_vars, default_vars)
        elif do_type == "list":
            return self.merge_list(key, instance_vars, default_vars)
        elif do_type == "dict":
            return self.merge_dict(key, instance_vars, default_vars)
        elif do_type == "map":
            return self.merge_map(key, instance_vars, default_vars)

    def pattern(self, esc='$'):
        regex = "\%s((<.*?>)|(\(.*?\))|({.*?})|(\[.*?\]))" % esc
        return re.compile(regex)

    def search(self, value, esc='$'):
        m = self.pattern(esc).search(value)
        if m is None:
            return None
        else:
            return m.group(0)

    def format_str(self, str_value, new_str):
        old_str = self.search(str_value)
        if old_str is None:
            return None
        else:
            return str_value.replace(old_str, new_str)

    def type_of(self, value):
        if not value:
            return None, None
        elif isinstance(value, basestring):
            key = self.search(value)
            if key is None:
                return None, None
            elif key[1] == "(" and key[-1] == ")" and '.' not in key:
                return "str", key[2:-1]
            elif key[1] == "[" and key[-1] == "]":
                return "list", key[2:-1]
            elif key[1] == "{" and key[-1] == "}":
                return "dict", key[2:-1]
            elif key[1] == "<" and key[-1] == ">" and '.' in key:
                return "map", key[2:-1]

        elif isinstance(value, dict):
            key = self.search(value.keys()[0])
            if key is None:
                return None, None
            elif key[1] == "[" and key[-1] == "]":
                if isinstance(value.values()[0], list):
                    return "list", key[2:-1]
            elif key[1] == "{" and key[-1] == "}":
                if isinstance(value.values()[0], dict):
                    return "dict", key[2:-1]
            elif key[1] == "<" and key[-1] == ">":
                return "func", key[2:-1]
        else:
            return None, None

    def tplsub_func(self, func, value, instance_vars=None, default_vars=None):
        if func in self.builtin:
            params = self.tplsub(value, instance_vars, default_vars)
            log.debug("Call the func '%s' with params '%s'" %
                     (func, params))
            try:
                if isinstance(params, dict):
                    return self.builtin[func](**params)
                elif isinstance(params, list):
                    return self.builtin[func](*params)
                elif not params:
                    return self.builtin[func]()
                else:
                    return self.builtin[func](params)
            except Exception:
                msg = traceback.format_exc()
                raise IcsException(
                    "Invalid function found: %s \n %s" % (func, msg))
        else:
            raise IcsException("Unknown function found: %s" % func)

    def tplsub_dict(self, dict_value, instance_vars=None, default_vars=None):
        do_type, func = self.type_of(dict_value)
        if do_type == "func":
            return self.tplsub_func(func, dict_value.values()[0],
                                    instance_vars, default_vars)
        else:
            results = {}
            for key, value in dict_value.items():
                results[key] = self.tplsub(value, instance_vars, default_vars)
            return results

    def tplsub_list(self, list_value, instance_vars=None, default_vars=None):
        results = []
        for value in list_value:
            results.append(self.tplsub(
                value, instance_vars, default_vars))

        return results

    def update_str(self, str_value, new_str,
                   instance_vars=None, default_vars=None):
        if isinstance(new_str, basestring):
            return self.tplsub_str(self.format_str(str_value, new_str),
                                   instance_vars, default_vars)
        elif self.type_of(new_str)[0] is None:
            return new_str
        else:
            new_str = self.tplsub(new_str, instance_vars, default_vars)
            return self.update_str(str_value, new_str,
                                   instance_vars, default_vars)

    def tplsub_str(self, str_value, instance_vars=None, default_vars=None):
        if self.type_of(str_value)[0] is None:
            return str_value
        log.debug("Fetching '%s'..." % str_value)
        new_str = self.do_sub(str_value, instance_vars, default_vars)
        return self.update_str(str_value, new_str, instance_vars, default_vars)

    def tplsub(self, value, instance_vars=None, default_vars=None):
        """
        Entry for JSON Template Substitution (dict)
        """
        # FIXME: JSON substitution itself
        if instance_vars is None and default_vars is None:
            instance_vars = value

        self.instance_vars = instance_vars
        self.default_vars = default_vars

        if isinstance(value, dict):
            return self.tplsub_dict(value, instance_vars, default_vars)
        elif isinstance(value, list):
            return self.tplsub_list(value, instance_vars, default_vars)
        elif isinstance(value, basestring):
            return self.tplsub_str(value, instance_vars, default_vars)
        elif isinstance(value, (int, float, bool)) or value is None:
            return value
        else:
            raise IcsException("Unexpetcted type: %s" % type(value))

    @staticmethod
    def strip_comment(data):
        return re.sub('^\s*#.*', '', data, flags=re.MULTILINE)

    @staticmethod
    def fp_to_json(fp, **kwargs):
        return json.loads(JsonSubs.strip_comment(fp.read()), **kwargs)

    def tplsubs(self, output_fp, instance_fp=None, default_fp=None):
        """
        Entry for JSON Template Substitution (fp)
        """
        output = instance_vars = default_vars = {}
        if output_fp is not None:
            output = self.fp_to_json(output_fp)
        if instance_fp is not None:
            instance_vars = self.fp_to_json(instance_fp)
        if default_fp is not None:
            default_vars = self.fp_to_json(default_fp)
        return self.tplsub(output, instance_vars, default_vars)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
