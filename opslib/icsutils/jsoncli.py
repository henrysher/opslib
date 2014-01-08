"""
JsonCli: Library for CLI based on JSON
--------------------------------------

+------------------------+-------------+
| This is the JsonCli common library.  |
+------------------------+-------------+
"""
import argparse
from collections import OrderedDict
from argcomplete import autocomplete
from botocore import xform_name


type_map = {
    'structure': str,
    'map': str,
    'timestamp': str,
    'list': str,
    'string': str,
    'float': float,
    'integer': int,
    'long': int,
    'boolean': bool,
    'double': float,
    'blob': str}


class OrderNamespace(argparse.Namespace):

    """
    Namespace with Order: from argparse.Namespace
    """
    __order__ = OrderedDict()

    def __init__(self, **kwargs):
        super(OrderNamespace, self).__init__(**kwargs)

    def __setattr__(self, attr, value):
        if value is not None:
            self.__order__[attr] = value
            super(OrderNamespace, self).__setattr__(attr, value)


def add_arguments(group, args):
    """
    Add Arguments to CLI
    """
    for kkk, vvv in args.iteritems():
        if 'type' in vvv and vvv['type'] in type_map:
            vvv['type'] = type_map[vvv['type']]
        if 'help' in vvv and not vvv['help']:
            vvv['help'] = argparse.SUPPRESS
        changed = xform_name(kkk, "-")
        if kkk != changed:
            kkk = "-".join(["", changed])
        group.add_argument(kkk, **vvv)
    return group


def recursive_parser(parser, args):
    """
    Recursive CLI Parser
    """
    subparser = parser.add_subparsers(help=args.get(
        '__help__', ''), dest=args.get('__dest__', ''))
    for k, v in args.iteritems():
        if k == '__help__' or k == '__dest__':
            continue
        group = subparser.add_parser(k, help=v.get('help', ''))
        for kk, vv in v.iteritems():
            if kk == 'Subparsers':
                group = recursive_parser(group, vv)
            elif kk == 'Arguments':
                group = add_arguments(group, vv)
    return parser


def parse_args(args):
    """
    Create the Command Line Interface

    :type args: dict
    :param args: describes the command structure for the CLI
    """
    parser = argparse.ArgumentParser(description=args.get('Description', ''))
    for k, v in args.iteritems():
        if k == 'Subparsers':
            parser = recursive_parser(parser, v)
        elif k == 'Arguments':
            parser = add_arguments(parser, v)
    autocomplete(parser)
    return parser.parse_args(None, OrderNamespace())

# vim: tabstop=4 shiftwidth=4 softtabstop=4
