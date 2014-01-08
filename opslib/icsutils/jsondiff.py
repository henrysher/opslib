"""
JsonDiff: Library for JSON DIFF
-------------------------------

+------------------------+-------------+
| This is the JsonDiff common library. |
+------------------------+-------------+
"""

try:
    import json
except ImportError:
    import simplejson as json

from opslib.icsexception import IcsException

import logging
log = logging.getLogger(__name__)


def is_scalar(value):
    """
    Primitive version, relying on the fact that JSON cannot
    contain any more complicated data structures.
    """
    return not isinstance(value, (list, tuple, dict))


class Comparator(object):

    """
    Main workhorse for JSON Comparator
    """

    def __init__(self, fp1=None, fp2=None,
                 include=[], exclude=[], ignore_add=False):
        """
        :type fp1: object
        :param fp1: file object (opened with read permission)

        :type fp2: object
        :param fp2: file object (opened with read permission)

        :type include: list
        :param include: a list of attributes to include in the comparison

        :type exclude: list
        :param exclude: a list of attributes to exclude in the comparison

        :type ignore_add: bool
        :param ignore_add: whether to ignore the added items in the comparison

        **Example:**

        >>> from opslib.icsutils.jsondiff import Comparator
        >>> import json
        >>> old_json = {
        ...     "name": "opslib",
        ...     "version": "1.2.0",
        ...     "members": {
        ...         "role": "ops",
        ...         "group": [ "ops", "devops" ]
        ...     }
        ... }
        >>> new_json = {
        ...     "name": "opslib",
        ...     "version": "1.3.0",
        ...     "members": {
        ...         "role": "devops",
        ...         "group": [ "devops" ]
        ...     }
        ... }
        >>> json.dump(old_json, open("old.json", "w"))
        >>> json.dump(new_json, open("new.json", "w"))
        >>> fp_old = open("old.json", "r")
        >>> fp_new = open("new.json", "r")
        >>> engine = Comparator(fp_old, fp_new)
        >>> res = engine.compare_dicts()
        >>> print json.dumps(res, sort_keys=True, indent=4)
        {
            "members": {
                "group": {
                    "0": {
                        "+++": "devops",
                        "---": "ops"
                    },
                    "1": {
                        "---": "devops"
                    }
                },
                "role": {
                    "+++": "devops",
                    "---": "ops"
                }
            },
            "version": {
                "+++": "1.3.0",
                "---": "1.2.0"
            }
        }

        """
        self.obj1 = None
        self.obj2 = None
        if fp1:
            try:
                self.obj1 = json.load(fp1)
            except (TypeError, OverflowError, ValueError), exc:
                raise IcsException("Cannot decode object from JSON.\n%s" %
                                   unicode(exc))
        if fp2:
            try:
                self.obj2 = json.load(fp2)
            except (TypeError, OverflowError, ValueError), exc:
                raise IcsException("Cannot decode object from JSON\n%s" %
                                   unicode(exc))

        self.excluded_attributes = []
        self.included_attributes = []
        self.ignore_added = False
        if include:
            self.included_attributes = include or []
        if exclude:
            self.excluded_attributes = exclude or []
        if ignore_add:
            self.ignore_added = ignore_add or False

    def _is_incex_key(self, key, value):
        """Is this key excluded or not among included ones? If yes, it should
        be ignored."""
        key_out = ((self.included_attributes and
                   (key not in self.included_attributes)) or
                   (key in self.excluded_attributes))
        value_out = True
        if isinstance(value, dict):
            for change_key in value:
                if isinstance(value[change_key], dict):
                    for key in value[change_key]:
                        if ((self.included_attributes and
                             (key in self.included_attributes)) or
                           (key not in self.excluded_attributes)):
                            value_out = False
        return key_out and value_out

    def _filter_results(self, result):
        """Whole -i or -x functionality. Rather than complicate logic while
        going through the object's tree we filter the result of plain
        comparison.

        Also clear out unused keys in result"""
        out_result = {}
        for change_type in result:
            temp_dict = {}
            for key in result[change_type]:
                log.debug("change_type = %s", change_type)
                if self.ignore_added and (change_type == "+++"):
                    continue
                log.debug("result[change_type] = %s, key = %s",
                          unicode(result[change_type]), key)
                log.debug("self._is_incex_key = %s",
                          self._is_incex_key(
                              key,
                              result[change_type][key]))
                if not self._is_incex_key(key, result[change_type][key]):
                    temp_dict[key] = result[change_type][key]
            if len(temp_dict) > 0:
                out_result[change_type] = temp_dict

        return out_result

    def _compare_elements(self, old, new):
        """Unify decision making on the leaf node level."""
        res = None
        # We want to go through the tree post-order
        if isinstance(old, dict):
            res_dict = self.compare_dicts(old, new)
            if (len(res_dict) > 0):
                res = res_dict
        # Now we are on the same level
        # different types, new value is new
        elif (type(old) != type(new)):
            res = {'---': old, '+++': new}
        # recursive arrays
        # we can be sure now, that both new and old are
        # of the same type
        elif (isinstance(old, list)):
            res_arr = self._compare_arrays(old, new)
            if (len(res_arr) > 0):
                res = res_arr
        # the only thing remaining are scalars
        else:
            scalar_diff = self._compare_scalars(old, new)
            if scalar_diff is not None:
                res = scalar_diff

        return res

    def _compare_scalars(self, old, new, name=None):
        """
        Be careful with the result of this function. Negative answer from this
        function is really None, not False, so deciding based on the return
        value like in

        if self._compare_scalars(...):

        leads to wrong answer (it should be
        if self._compare_scalars(...) is not None:)
        """
        # Explicitly excluded arguments
        if old != new:
            return {'---': old, '+++': new}
        else:
            return None

    def _compare_arrays(self, old_arr, new_arr):
        """
        simpler version of compare_dicts; just an internal method, because
        it could never be called from outside.

        We have it guaranteed that both new_arr and old_arr are of type list.
        """
        inters = min(len(old_arr), len(new_arr))  # this is the smaller length

        result = {
            u"+++": {},
            u"---": {},
        }

        for idx in range(inters):
            res = self._compare_elements(old_arr[idx], new_arr[idx])
            if res is not None:
                result[idx] = res

        # the rest of the larger array
        if (inters == len(old_arr)):
            for idx in range(inters, len(new_arr)):
                result[idx] = {u'+++':  new_arr[idx]}
        else:
            for idx in range(inters, len(old_arr)):
                result[idx] = {u'---': old_arr[idx]}

        # Clear out unused keys in result
        out_result = {}
        for key in result:
            if len(result[key]) > 0:
                out_result[key] = result[key]

        return self._filter_results(result)

    def compare_dicts(self, old_obj=None, new_obj=None):
        """
        The real workhorse
        """
        if not old_obj and hasattr(self, "obj1"):
            old_obj = self.obj1
        if not new_obj and hasattr(self, "obj2"):
            new_obj = self.obj2

        old_keys = set()
        new_keys = set()
        if old_obj and len(old_obj) > 0:
            old_keys = set(old_obj.keys())
        if new_obj and len(new_obj) > 0:
            new_keys = set(new_obj.keys())

        keys = old_keys | new_keys

        result = {
            u"+++": {},
            u"---": {},
        }
        for name in keys:
            # old_obj is missing
            if name not in old_obj:
                result[u'+++'][name] = new_obj[name]
            # new_obj is missing
            elif name not in new_obj:
                result[u'---'][name] = old_obj[name]
            else:
                res = self._compare_elements(old_obj[name], new_obj[name])
                if res is not None:
                    result[name] = res

        return self._filter_results(result)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
