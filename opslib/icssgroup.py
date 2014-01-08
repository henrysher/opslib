"""
IcsSecurityGroup: Library for AWS Security group
------------------------------------------------

+--------------------+------------+-----------+
| This is the IcsSeurityGroup common library. |
+--------------------+------------+-----------+
"""
import traceback
from boto.ec2 import get_region
from boto.ec2.connection import EC2Connection
from boto.rds import connect_to_region

import logging
log = logging.getLogger(__name__)


class IcsSGroup(object):

    """
    Library for AWS Security group
    """

    def __init__(self, region, **kwargs):
        self.conn = EC2Connection(region=get_region(region), **kwargs)
        self.rds = connect_to_region(region, **kwargs)

    def create_rds_group(self, name, description=None):
        """
        Create a new security group for your account.
        This will create the security group within the region
        you are currently connected to.

        :param name: The name of the new security group
        :type name: string

        :param description: he description of the new security group
        :type description: string

        :return: The newly created DBSecurityGroup
        :type: boto.rds.dbsecuritygroup.DBSecurityGroup
        """

        return self.rds.create_dbsecurity_group(name, description)

    def create_group(self, name, description, vpc_id=None):
        """
        Create a new security group for your account. This will create
        the security group within the region you are currently connected to.

        :param name: The name of the new security group
        :type name: string

        :param description: The description of the new security group
        :type description: string

        :param vpc_id: The ID of the VPC to create the security group in.
        :type vpc_id: string

        :return: The newly created boto.ec2.securitygroup.SecurityGroup.
        :type: boto.ec2.securitygroup.SecurityGroup

        """

        return self.conn.create_security_group(name, description, vpc_id)

    def rds_authorize_group(self, group_name, cidr_ip=None,
                            src_group_name=None, src_group_owner_id=None):
        """
        Add a new rule to an existing security group.
        You need to pass in either src_security_group_name and
        src_security_group_owner_id OR a CIDR block but not both.

        :param group_name: The name of the security group adding the rule to.
        :type group_name: string

        :param cidr_ip: The CIDR block you are providing access to.
        :type cidr_ip: string

        :param src_group_name: The name of the EC2 security group you are
                               granting access to.
        :type src_group_name: string

        :param src_group_owner_id: The ID of the owner of the EC2 security
                                   group you are granting access to.
        :type src_group_owner_id: string

        :return: True if successful.
        :tyep: bool
        """

        return self.rds.authorize_dbsecurity_group(
            group_name,
            cidr_ip=cidr_ip,
            ec2_security_group_name=src_group_name,
            ec2_security_group_owner_id=src_group_owner_id)

    def add_ingress_rules(self, group_name, src_group=None,
                          ip_protocol=None, from_port=None, to_port=None,
                          cidr_ip=None, group_id=None, src_group_id=None):
        """
        Add a new rule to an existing security group.
        You need to pass in either src_security_group_name OR ip_protocol,
        from_port, to_port, and cidr_ip. In other words,
        either you are authorizing another group or
        you are authorizing some ip-based rule.

        :param group_name: The name of the security group you are
                           adding the rule to
        :type group_name: string

        :param src_security_group_name: The name of the security group
                                        you are granting access to
        :type src_security_group_name: string

        :param ip_protocol: Either tcp | udp | icmp
        :type ip_protocol: string

        :param from_port: The beginning port number you are enabling
        :type from_port: int

        :param to_port: The ending port number you are enabling
        :type to_port: int

        :param cidr: The CIDR block you are providing access to
        :type cidr: list of strings

        :param group_id: ID of the EC2 or VPC security group to modify.
                         This is required for VPC security groups and can
                         be used instead of group_name for EC2 security groups
        :type group_id: string

        :return: True if successful.
        :type: bool

        """

        return self.conn.authorize_security_group(
            group_name=group_name,
            src_security_group_name=src_group,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip=cidr_ip,
            group_id=group_id,
            src_security_group_group_id=src_group_id)

    def add_egress_rules(self, group_id, ip_protocol, from_port=None,
                         to_port=None, cidr_ip=None, des_group_id=None):
        """
        The action adds one or more egress rules to a VPC security group

        :param group_id: ID of theVPC security group to modify
        :type group_id: str

        :param ip_protocol: Either tcp | udp | icmp
        :type ip_protocol: string

        :param from_port: The beginning port number you are enabling
        :type from_port: int

        :param to_port: The ending port number you are enabling
        :type to_port: int

        :param cidr_ip: The CIDR block you are providing access to
        :type cidr_ip: list of strings

        :param des_group_id: The ID of destination security groups
                              in the same VPC
        :type des_group_id: str
        """

        self.conn.authorize_security_group_egress(
            group_id=group_id,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip=cidr_ip,
            des_group_id=des_group_id)

    def rds_revoke_rules(self, group_name, src_group_name=None,
                         src_group_owner_id=None, cidr_ip=None):
        """
        Remove an existing rule from an existing security group.
        You need to pass in either ec2_security_group_name and
        ec2_security_group_owner_id OR a CIDR block.

        :param group_name: The name of the security group you are
                           removing the rule from.
        :type group_name: string

        :param src_group_name: The name of the EC2 security group
                               from which you are removing access.
        :type src_group_name: string

        :param src_group_owner_id: The ID of the owner of the EC2
                                   security from which you are removing access.
        :type src_group_owner_id: string

        :param cidr_ip: The CIDR block from which you are removing access.
        :type cidr_ip: string

        :return: True if successful.
        :type: bool
        """

        return self.rds.revoke_dbsecurity_group(
            group_name,
            ec2_security_group_name=src_group_name,
            ec2_security_group_owner_id=src_group_owner_id,
            cidr_ip=cidr_ip)

    def remove_ingress_rules(self, group_name, src_group=None,
                             ip_protocol=None, from_port=None, to_port=None,
                             cidr_ip=None, group_id=None, src_group_id=None):
        """
        Remove an existing rule from an existing security group

        :param group_name: The name of the security group you are removing
                           the rule from
        :type group_name: string

        :param src_security_group_name: The name of the security group
                                        you are revoking access to
        :type src_security_group_name: string

        :param ip_protocol: Either tcp | udp | icmp
        :type ip_protocol: string

        :param from_port: The beginning port number you are disabling
        :type from_port: int

        :param to_port: The ending port number you are disabling
        :type to_port: int

        :param cidr: The CIDR block you are revoking access to
        :type cidr: list of strings

        :param group_id: ID of the EC2 or VPC security group to modify.
                         This is required for VPC security groups and can
                         be used instead of group_name for EC2 security groups
        :type group_id: string

        :return: True if successful.
        :type: bool

        """

        return self.conn.revoke_security_group(
            group_name=group_name,
            src_security_group_name=src_group,
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip=cidr_ip,
            group_id=group_id,
            src_security_group_group_id=src_group_id)

    def get_security_groups(self, groupnames=None,
                            group_ids=None, filters=None):
        """
        Get all security groups associated with your account in a region.

        :param groupnames:  A list of the names of security groups to retrieve.
                          If not provided, all security groups will be returned
        :type groupnames: list

        :param group_ids:  A list of IDs of security groups to retrieve for
                           security groups within a VPC
        :type group_ids: list

        :param filters: Optional filters that can be used to limit the results
                        returned. Filters are provided in the form of a
                        dictionary consisting of filter names as the key and
                        filter values as the value. The set of allowable
                        filter names/values is dependent on the request being
                        performed.
        :type filters: dict
        """

        return self.conn.get_all_security_groups(
            groupnames=groupnames,
            group_ids=group_ids, filters=filters)
