#!/usr/local/bin/python


"""
IcsXxx: Library for Xxx
-----------------------

+--------------------+------------+--+
| This is the IcsXxx common library. |
+--------------------+------------+--+
"""

from icsexception import IcsXxxException


class IcsXxx(object):
    """
    ICS Library for Xxx
    """
    def __init__(self, region, **kwargs):
        self.conn = EC2Connection(region=get_region(region), **kwargs)

    def get_eips_from_addr(self, eip_list):
        """
        Get EIP objects via the list of EIP addresses

        :type eip_list: list
        :param eip_list: the list of EIP addresses

        :rtype: class
        :return: EIP objects in boto
        """
        return self.conn.get_all_addresses(
            filters={'public-ip': eip_list})

# vim: tabstop=4 shiftwidth=4 softtabstop=4
