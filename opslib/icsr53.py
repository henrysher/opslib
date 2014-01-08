"""
IcsR53: Library for Route53
---------------------------

+--------------------+------------+--+
| This is the IcsR53 common library. |
+--------------------+------------+--+
"""

import time
import string

from boto.route53 import Route53Connection
#from boto.route53.zone import Zone
from boto.route53.record import ResourceRecordSets
from boto.route53 import exception
from opslib.icsexception import IcsR53Exception
from opslib.zone import Zone

import logging
log = logging.getLogger(__name__)


class IcsR53(object):

    """
    ICS Library for R53
    """

    def __init__(self, dns_name=None, **kwargs):
        self.r53 = Route53Connection(**kwargs)
        if dns_name is not None:
            self.zone = self.get_zone(dns_name)
            if not self.zone:
                raise IcsR53Exception(
                    "Can't find DNS Zone for '%s'" % (dns_name))

    @staticmethod
    def parse_dns_name(name):
        """
        Parse the value of Tag "DnsName"

        :type name: string
        :param name: the value of Instance Tag "DnsName"
            for example, "test.example.com:A:Public:1"

        :rtype: tuple
        :return: a tuple containing (DnsName, DnsType, Public/Private, Weight)
            for example, ("test.example.com", "A", True, "10")
        """
        if name is None or not isinstance(name, basestring):
            raise IcsR53Exception(
                "DnsName should be a 'str' not %s" % type(name))

        name = name.split(':', 3)
        if len(name) < 3 or len(name) > 4:
            raise IcsR53Exception(
                "Invalid number of sub-strings: '%s'" % len(name))
        if name[1].upper() not in ("A", "CNAME"):
            raise IcsR53Exception(
                "Invalid DNS type: 'A' or 'CNAME', not '%s'" % name[1])
        if name[2].lower() not in ("public", "private"):
            raise IcsR53Exception(
                "Invalid DNS value: 'public' or 'private', not '%s'" % name[2])

        if len(name) == 4:
            return(name[0].lower(), name[1].upper(),
                   name[2].lower() == "public",
                   string.atoi(name[3]).__str__())

        return(name[0].lower(), name[1].upper(),
               name[2].lower() == "public",
               None)

    def get_zone_id(self):
        """
        Get the hosted zone ID for the specified domain name

        :rtype: string
        :return: a string containing the ID of the specified hosted zone
        """
        return self.zone.id

    def get_zone(self, name):
        """
        Get the hosted zone for the specified domain name

        :type name: string
        :param name: the specified domain name

        :rtype: class
        :return: a class containing the specified hosted zone
        """
        zone_dict = self.get_zone_dict(name)
        return Zone(self.r53, zone_dict)

    def set_zone(self, name):
        """
        Set the hosted zone for the specified domain name

        :type name: string
        :param name: the specified domain name
        """
        self.zone = self.get_zone(name)

    def get_zone_dict(self, name):
        """
        Get the hosted zone info for the specified domain name

        :type name: string
        :param name: the specified domain name

        :rtype: dict
        :return: a dict containing the specified hosted zone info
        """
        if name is None or not isinstance(name, basestring):
            raise IcsR53Exception(
                "DnsName should be a 'str' not %s" % type(name))
        name = name.lower()
        name = self.r53._make_qualified(name)
        results = self.r53.get_all_hosted_zones()
        zones = results['ListHostedZonesResponse']['HostedZones']
        zones.sort(key=len, reverse=True)
        zones_matched = {}
        for zone in zones:
            zname = zone['Name'].lower()
            if len(zname) > len(name):
                continue
            if len(zname) < len(name) and name[-1 - len(zname)] != '.':
                continue
            if zname == name[-len(zname):]:
                zones_matched[zname] = zone
        if zones_matched:
            znames = zones_matched.keys()
            znames.sort(key=len, reverse=True)
            return zones_matched[znames[0]]
        return None

    def get_records(self):
        """
        Return a ResourceRecordsSets for all of the records in this zone.
        """
        return self.zone.get_records()

    def find_all_records(self):
        """
        Search all records in this zone.
        """
        return self.zone.find_all_records()

    def find_records(self, name, type, desired=1, all=False, identifier=None):
        """
        Search this Zone for records that match given parameters.
        Returns None if no results, a ResourceRecord if one result, or
        a ResourceRecordSets if more than one result.

        :type name: str
        :param name: The name of the records should match this parameter

        :type type: str
        :param type: The type of the records should match this parameter

        :type desired: int
        :param desired: The number of desired results.  If the number of
           matching records in the Zone exceeds the value of this parameter,
           throw TooManyRecordsException

        :type all: Boolean
        :param all: If true return all records that match name, type, and
          identifier parameters

        :type identifier: Tuple
        :param identifier: A tuple specifying WRR or LBR attributes.  Valid
           forms are:

           * (str, str): WRR record [e.g. ('foo','10')]
           * (str, str): LBR record [e.g. ('foo','us-east-1')

        """
        return self.zone.find_records(name, type, desired,
                                      all, identifier)

    def wait_to_complete(self, status=None, timeout=60):
        """
        Wait for the Route53 commit change to complete

        :type status: class
        :param status: the instance initializing ``boto.route53.status.Status``
        """
        for i in xrange(timeout / 5):
            result = status.update()

            if result == 'INSYNC':
                return True
            elif result != 'PENDING':
                raise IcsR53Exception("Unexpected status found: %s" % result)
            time.sleep(5)

        result = status.update()
        if result == 'INSYNC':
            return True
        else:
            raise IcsR53Exception("Wait until timeout: %ss" % timeout)

    def add_record(self, resource_type, name, value, ttl=60,
                   identifier=None):
        """
        Add a new record to this Zone.  See _new_record for parameter
        documentation.  Returns a Status object.
        """
        return self.zone.add_record(self,
                                    resource_type,
                                    name, value, ttl,
                                    identifier)

    def update_record(self, old_record, new_value, new_ttl=None,
                      new_identifier=None):
        """
        Update an existing record in this Zone.  Returns a Status object.

        :type old_record: ResourceRecord
        :param old_record: A ResourceRecord (e.g. returned by find_records)

        See _new_record for additional parameter documentation.
        """
        return self.zone.update_record(old_record, new_value,
                                       new_ttl, new_identifier)

    def delete_record(self, record):
        """
        Delete one or more records from this Zone.  Returns a Status object.

        :param record: A ResourceRecord (e.g. returned by
           find_records) or list, tuple, or set of ResourceRecords.
        """
        return self.zone.delete_record(record)

    def add_cname(self, name, value, ttl=None, identifier=None):
        """
        Add a new CNAME record to this Zone.  See _new_record for
        parameter documentation.  Returns a Status object.
        """
        return self.zone.add_cname(name, value, ttl, identifier)

    def add_a(self, name, value, ttl=None, identifier=None):
        """
        Add a new A record to this Zone.  See _new_record for
        parameter documentation.  Returns a Status object.
        """
        return self.zone.add_a(name, value, ttl, identifier)

    def add_alias(self, name, type, alias_hosted_zone_id,
                  alias_dns_name, identifier=None):
        """
        Add a new alias record to this Zone.  See _new_alias_record for
        parameter documentation.  Returns a Status object.
        """
        return self.zone.add_alias(name, type, alias_hosted_zone_id,
                                   alias_dns_name, identifier)

    def get_cname(self, name, identifier=None, all=False):
        """
        Search this Zone for CNAME records that match name.

        Returns a ResourceRecord.

        If there is more than one match return all as a
        ResourceRecordSets if all is True, otherwise throws
        TooManyRecordsException.
        """
        return self.zone.find_records(name, 'CNAME',
                                      identifier=identifier,
                                      all=all)

    def get_a(self, name, identifier=None, all=False):
        """
        Search this Zone for A records that match name.

        Returns a ResourceRecord.

        If there is more than one match return all as a
        ResourceRecordSets if all is True, otherwise throws
        TooManyRecordsException.
        """
        return self.zone.find_records(name, 'A',
                                      identifier=identifier,
                                      all=all)

    def update_cname(self, name, value, ttl=None, identifier=None):
        """
        Update the given CNAME record in this Zone to a new value, ttl,
        and identifier.  Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        name = self.r53._make_qualified(name)
        value = self.r53._make_qualified(value)
        old_record = self.get_cname(name, identifier)
        if old_record is None:
            return None
        else:
            ttl = ttl or old_record.ttl
            return self.update_record(old_record,
                                      new_value=value,
                                      new_ttl=ttl,
                                      new_identifier=identifier)

    def update_a(self, name, value, ttl=None, identifier=None):
        """
        Update the given A record in this Zone to a new value, ttl,
        and identifier.  Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        name = self.r53._make_qualified(name)
        old_record = self.get_a(name, identifier)
        if old_record is None:
            return None
        else:
            ttl = ttl or old_record.ttl
            return self.update_record(old_record,
                                      new_value=value,
                                      new_ttl=ttl,
                                      new_identifier=identifier)

    def update_alias(self, name, type, identifier=None, alias_dns_name=None):
        """
        Update the given alias record in this Zone to a new routing policy
        Returns a Status object.

        Will throw TooManyRecordsException is name, value does not match
        a single record.
        """
        return self.zone.update_alias(name, type, identifier, alias_dns_name)

    def delete_cname(self, name, identifier=None, all=False):
        """
        Delete a CNAME record matching name and identifier from
        this Zone.  Returns a Status object.

        If there is more than one match delete all matching records if
        all is True, otherwise throws TooManyRecordsException.
        """
        return self.zone.delete_cname(name, identifier)

    def delete_a(self, name, identifier=None, all=False):
        """
        Delete an A record matching name and identifier from this
        Zone.  Returns a Status object.

        If there is more than one match delete all matching records if
        all is True, otherwise throws TooManyRecordsException.
        """
        return self.zone.delete_a(name, identifier, all)


# vim: tabstop=4 shiftwidth=4 softtabstop=4
