"""
IcsELB: Library for ELB
-----------------------

+--------------------+------------+--+
| This is the IcsELB common library. |
+--------------------+------------+--+
"""

import opslib
from boto.ec2.elb import connect_to_region
from boto.ec2.elb import HealthCheck

import logging
log = logging.getLogger(__name__)


class IcsELB(object):

    """
    ICS Library for ELB
    """

    def __init__(self, region, **kwargs):
        self.conn = connect_to_region(region, **kwargs)

    def get_elb_id(self, name):
        """
        Get Load Balancer Hosted Zone ID

        :type name: str
        :param name: The load balances name

        :rtype: str
        :retrun: load balancer hosted zone id
        """

        record = self.conn.get_all_load_balancers(name)
        return record[0].canonical_hosted_zone_name_id

    def get_elb_dns_name(self, name):
        """
        Get Load Balancer DNS name.
        :type name: str
        :param name: The load balances name

        :rtype: str
        :retrun: load balancer hosted zone id
        """

        record = self.conn.get_all_load_balancers(name)
        return record[0].dns_name

    def get_elb_health(self, name, instance_id):
        """
        check the health of the specified instance in the specified elb

        :type name: string
        :param name: The load balances name

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: boolean or string
        :return: False or out of service reason
        """
        id_list = []
        id_list.append(instance_id)

        try:
            elb = self.conn.describe_instance_health(name, instances=id_list)
        except Exception:
            return 'Cannot find this elb: %s' % name

        if elb[0].state == 'InService':
            return False
        else:
            return elb[0].reason_code

    def parse_listeners(self, listeners):
        """
        Parse elb listeners form list of string to list of tuple

        :param listeners: Listeners of this elb
        :type listeners: list of string

        :return: The list of listeners tuple
        :type: list of tuple
        """

        l_list = []
        for l in listeners:
            l = l.split(",")
            if l[2] == 'HTTPS':
                l_list.append((int(l[0]), int(l[1]), l[2], l[3]))
            else:
                l_list.append((int(l[0]), int(l[1]), l[2]))

        return l_list

    def set_health_check(self, name, health_check):
        """
        Configures the health check behavior for the instances behind this
        load balancer.

        :param name: The mnemonic name associated with the load balancer
        :type name: string

        :param health_check: A HealthCheck instance that tells the load
                             balancer how to check its instances for health.
        :type health_check: boto.ec2.elb.healthcheck.HealthCheck
        """

        hc = HealthCheck(timeout=int(health_check[0]),
                         interval=int(health_check[1]),
                         unhealthy_threshold=int(health_check[2]),
                         healthy_threshold=int(health_check[3]),
                         target=health_check[4])
        self.conn.configure_health_check(name, hc)

    def create_elb(self, name, zones, listeners=None,
                   subnets=None, groups=None):
        """Create an ELB named <name>

        :param name: The mnemonic name associated with the new load balancer
        :type name: string

        :param zones: The names of the availability zone(s) to add
        :type zones: list of strings

        :param listeners:  Each tuple contains three or four values:

        * LoadBalancerPortNumber and InstancePortNumber are \
            integer values between 1 and 65535;
        * Protocol is a string containing 'TCP', 'SSL', 'HTTP', 'HTTPS';
        * SSLCertificateID is the ARN of a AWS AIM certificate, \
            and must be specified when doing HTTPS

        :type listeners: List of string

        :param subnets:  A list of subnet IDs in your VPC
                         to attach to your LoadBalancer
        :type subnets: list of strings

        :param groups: The security groups assigned to
                               your LoadBalancer within your VPC
        :type groups: list of strings
        """

        l_list = self.parse_listeners(listeners)

        if subnets and groups:
            area = None
            self.conn.create_load_balancer(name, area, l_list,
                                           subnets=subnets,
                                           security_groups=groups)
        else:
            self.conn.create_load_balancer(name, zones, l_list)

    def remove_elb_listeners(self, name, listeners):
        """
        Remove a Listener (or group of listeners) for an existing
        Load Balancer

        :param name: The name of the load balancer to create the listeners for
        :type name: string

        :param listeners: Each int represents the port on the ELB
                          to be removed
        :type listeners: List int
        """

        self.conn.delete_load_balancer_listeners(name, listeners)

    def set_elb_listeners(self, name, listeners):
        """
        Create a Listener (or group of listeners) for an existing
        Load Balancer

        :param name: The name of the load balancer to create the listeners for
        :type name: string

        :param listeners: Listener to be setted
        :type new_listeners: List of string
        """

        l_list = self.parse_listeners(listeners)
        self.conn.create_load_balancer_listeners(name, listeners=l_list)

    def get_all_elbs(self, load_balancer_names=None):
        """
        Get all load balancers in this region

        :param load_balancer_names: An optional list of load balancer names
        :type load_balancer_names: list

        :rtype: boto.resultset.ResultSet
        :return: A ResultSet containing instances of
                 boto.ec2.elb.loadbalancer.LoadBalancer
        """

        return self.conn.get_all_load_balancers(load_balancer_names)

    def delete_elb(self, name):
        """
        Remove an load balancers from your account

        :param name: The name of the Load Balancer to delete
        :type name: string
        """

        self.conn.delete_load_balancer(name)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
