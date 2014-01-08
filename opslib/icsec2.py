"""
IcsEc2: Library for EC2
-----------------------

+--------------------+------------+--+
| This is the IcsEc2 common library. |
+--------------------+------------+--+
"""

from operator import attrgetter
from time import time, mktime, sleep, gmtime, strftime, strptime

from boto.ec2 import get_region
from boto.ec2.connection import EC2Connection
from boto.vpc import connect_to_region as vpc_connect_to_region
from opslib.icsexception import IcsEc2Exception

import logging
log = logging.getLogger(__name__)


class IcsEc2(EC2Connection):

    """
    ICS Library for EC2
    """

    def __init__(self, region, **kwargs):
        super(IcsEc2, self).__init__(
            region=get_region(region), **kwargs)

    def get_instance_attribute(self, instance_id, attr_name):
        """
        Get the attribute value of an instance.

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :type attr_name: string
        :param attr_name: the name of the instance attribute,
            details shown as below:

        :ivar id: The unique ID of the Instance.
        :ivar groups: A list of Group objects representing the security
            groups associated with the instance.
        :ivar public_dns_name: The public dns name of the instance.
        :ivar private_dns_name: The private dns name of the instance.
        :ivar state: The string representation of the instance's current state.
        :ivar state_code: An integer representation of the instance's
            current state.
        :ivar previous_state: The string representation of the instance's
            previous state.
        :ivar previous_state_code: An integer representation of the
            instance's current state.
        :ivar key_name: The name of the SSH key associated with the instance.
        :ivar instance_type: The type of instance (e.g. m1.small).
        :ivar launch_time: The time the instance was launched.
        :ivar image_id: The ID of the AMI used to launch this instance.
        :ivar placement: The availability zone in which the instance is
            running.
        :ivar placement_group: The name of the placement group the instance
            is in (for cluster compute instances).
        :ivar placement_tenancy: The tenancy of the instance, if the instance
            is running within a VPC. An instance with a tenancy of dedicated
            runs on a single-tenant hardware.
        :ivar kernel: The kernel associated with the instance.
        :ivar ramdisk: The ramdisk associated with the instance.
        :ivar architecture: The architecture of the image (i386|x86_64).
        :ivar hypervisor: The hypervisor used.
        :ivar virtualization_type: The type of virtualization used.
        :ivar product_codes: A list of product codes associated with
            this instance.
        :ivar ami_launch_index: This instances position within
            it's launch group.
        :ivar monitored: A boolean indicating whether monitoring is
            enabled or not.
        :ivar monitoring_state: A string value that contains the actual value
            of the monitoring element returned by EC2.
        :ivar spot_instance_request_id: The ID of the spot instance request
            if this is a spot instance.
        :ivar subnet_id: The VPC Subnet ID, if running in VPC.
        :ivar vpc_id: The VPC ID, if running in VPC.
        :ivar private_ip_address: The private IP address of the instance.
        :ivar ip_address: The public IP address of the instance.
        :ivar platform: Platform of the instance (e.g. Windows)
        :ivar root_device_name: The name of the root device.
        :ivar root_device_type: The root device type (ebs|instance-store).
        :ivar block_device_mapping: The Block Device Mapping for the instance.
        :ivar state_reason: The reason for the most recent state transition.
        :ivar groups: List of security Groups associated with the instance.
        :ivar interfaces: List of Elastic Network Interfaces associated with
            this instance.
        :ivar ebs_optimized: Whether instance is using optimized EBS volumes
            or not.
        :ivar instance_profile: A Python dict containing the instance
            profile id and arn associated with this instance.
        """
        if not isinstance(instance_id, basestring):
            raise IcsEc2Exception(
                "instance_id should be a 'str' not %s" % type(instance_id))
        if not isinstance(attr_name, basestring):
            raise IcsEc2Exception(
                "attr_name should be a 'str' not %s" % type(attr_name))

        resource = self.get_all_instances(instance_ids=instance_id)[0]
        instance = resource.instances[0]
        return attrgetter(attr_name)(instance)

    def get_public_address(self, instance_id):
        """
        Get the public IPv4 address of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: string
        :return: a string containing the public IPv4 address
        """
        return self.get_instance_attribute(instance_id, "ip_address")

    def get_private_address(self, instance_id):
        """
        Get the private IPv4 address of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: string
        :return: a string containing the private IPv4 address
        """
        return self.get_instance_attribute(instance_id, "private_ip_address")

    def get_public_dns(self, instance_id):
        """
        Get the public dns address of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: string
        :return: a string containing the public dns address
        """
        return self.get_instance_attribute(instance_id, "public_dns_name")

    def get_private_dns(self, instance_id):
        """
        Get the private dns address of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: string
        :return: a string containing the private IPv4 address
        """
        return self.get_instance_attribute(instance_id,
                                           "private_dns_name")

    def get_instance_tags(self, instance_id):
        """
        Get tags of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: dict
        :return: a dictionary containing the tags of this instance
        """
        tags = self.get_all_tags(filters={"resource-id": instance_id})
        ret = {}
        for tag in tags:
            ret.update({tag.name: tag.value})
        return ret

    def add_instance_tags(self, instance_id, tags):
        """
        Add tags to the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'
        """
        return self.create_tags(instance_id, tags)

    def del_instance_tags(self, instance_id, tags):
        """
        Remove tags of the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'
        """
        return self.delete_tags(instance_id, tags)

    def get_eips_from_addr(self, eip_list):
        """
        Get EIP objects via the list of EIP addresses

        :type eip_list: list
        :param eip_list: the list of EIP addresses

        :rtype: class
        :return: EIP objects in boto
        """
        return self.get_all_addresses(
            filters={'public-ip': eip_list})

    def get_eips_from_instance(self, instance_id):
        """
        Get EIP objects via the instance id

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: class
        :return: EIP objects in boto
        """
        return self.get_all_addresses(
            filters={'instance-id': instance_id})

    def get_instance_event(self, instance_id):
        """
        Get the event of the specified instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'
        """
        result = self.get_all_instance_status(
            instance_ids=instance_id)
        return result[0].events

    def get_instance_status(self, instance_id):
        """
        Get the instance status and system status
            of the specified instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: tuple
        :return: a tuple contains (instance_status, system_status)
        """
        inst_status = self.get_all_instance_status(
            instance_ids=instance_id)
        return (inst_status[0].instance_status.status,
                inst_status[0].system_status.status)

    def is_instance_healthy(self, instance_id):
        """
        check the health of the specified instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: boolean
        :return: True/False
        """
        result = self.get_instance_status(instance_id)
        if result[0].lower() == "ok" and result[1].lower() == "ok":
            return True
        else:
            return False

    def is_eip_free(self, eip):
        """
        check the availability of the specified EIP address: free or not

        :type eip: string
        :param eip: one EIP address

        :rtype: tuple
        :return: (True/False, EIP object/None)
        """
        eip_ops = self.get_eips_from_addr(eip)
        if not eip_ops:
            return (False, None)
        eip_op = eip_ops[0]
        if eip_op.public_ip != eip:
            raise IcsEc2Exception(
                "the real eip address %s is not equal to the expected one %s"
                % (eip_op.public_ip, eip))
        if eip_op.instance_id:
            return (False, eip_op)
        else:
            return (True, eip_op)

    def bind_eip(self, eip, instance_id):
        """
        Bind EIP address to the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: bool
        :return: success or raise IcsEc2Exception
        """
        if isinstance(eip, list):
            raise IcsEc2Exception(
                "cannot associate multiple eips '%s' to one instance '%s'"
                % (eip, instance_id))

        result, eipop = self.is_eip_free(eip)
        if result:
            log.info("the eip address " +
                     "'%s' will be associated " % eip +
                     "with this instance '%s'"
                     % instance_id)
            if eipop.domain == "vpc":
                self.associate_address(
                    instance_id=instance_id, allocation_id=eipop.allocation_id)
            else:
                eipop.associate(instance_id=instance_id)
        elif eipop.instance_id != instance_id:
            log.warning(
                "this eip '%s' has been associated with another '%s'"
                % (eip, eipop.instance_id))
            return False
        else:
            log.info("the eip address " +
                     "'%s' has been associated " % eip +
                     "with this instance '%s'"
                     % instance_id)
            return True

        result, eipop = self.is_eip_free(eip)
        return not result and eipop.instance_id == instance_id

    def free_eip(self, eip, instance_id):
        """
        Free EIP address to the instance

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: bool
        :return: success or raise IcsEc2Exception
        """
        if isinstance(eip, list):
            raise IcsEc2Exception(
                "cannot free multiple eips '%s' to one instance '%s'"
                % (eip, instance_id))

        result, eipop = self.is_eip_free(eip)
        if result:
            log.warning("this eip '%s' is not associated with '%s'"
                        % (eip, instance_id))
            return True
        elif eipop.instance_id != instance_id:
            log.warning(
                "this eip '%s' has been associated with another '%s'"
                % (eip, eipop.instance_id))
            return True

        log.info("the eip address " +
                 "'%s' will be disassociated with this instance '%s'"
                 % (eip, instance_id))

        eipop.disassociate()
        return self.is_eip_free(eip)[0]

    def get_volumes_by_instance(self, instance_id):
        """
        Get boto Volume Objects by instance Id

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: list
        :return: list of boto volume objects
        """
        return self.get_all_volumes(filters={'instance-id': instance_id})

    def take_snapshot(self, volume_id, description=None, tags=None):
        """
        Take a snapshot to existing volume with specific tags

        :type volume_id: string
        :param volume_id: EC2 volume id startwith 'vol-xxxxxxx'

        :type description: string
        :param description: words to describe the usage of this snapshot

        :type tags: dict
        :param tags: snapshot tags like {'Name': 'XXX'}

        :rtype: class
        :return: boto snapshot object
        """
        if tags is None:
            tags = {}

        snapshot = self.create_snapshot(volume_id, description)

        tags.update({'VolumeId': volume_id})
        timestamp = strftime("%Y%m%d-%H%M", gmtime())
        tags.update({'Timestamp': timestamp})

        for name, value in tags.iteritems():
            if not name.startswith('tag:'):
                name = name.replace('_', '-')
            else:
                name = name.replace('tag:', '')
            snapshot.add_tag(name, value)
        return snapshot

    @staticmethod
    def format_tags(tags):
        """
        Convert {"Name": "XXX"} to {"tag:Name": "XXX"}
        """
        new_tags = {}
        for name, value in tags.iteritems():
            if not name.startswith('tag:'):
                name = 'tag:'.join(["", name])
            new_tags[name] = value
        return new_tags

    def find_snapshot_by_tags(self, tags):
        """
        Find a snapshot by specific tags

        :type tags: dict
        :param tags: snapshot tags like {'Name': 'XXX'}

        :rtype: list
        :return: list of boto snapshot objects
        """
        tags = self.format_tags(tags)

        # FIXME: only used for Cassandra
        if 'tag:Timestamp' in tags and tags['tag:Timestamp'] == '0':
            refined_tags = {}
            refined_tags['tag:Role'] = tags['tag:Role']
            refined_tags['tag:Timestamp'] = tags['tag:Timestamp']
            tags = refined_tags

        return self.get_all_snapshots(filters=self.format_tags(tags))

    def fetch_latest_snapshot(self, snapshots):
        """
        Find the latest Snapshot
        """
        timestamps = [snapshot.tags['Timestamp'] for snapshot in snapshots]
        return snapshots[timestamps.index(max(timestamps))]

    def fetch_snapid_by_tags(self, **tags):
        """
        Find the Snapshot Id by specific tags

        :type tags: dict
        :param tags: snapshot tags like {'Name': 'XXX'}

        :rtype: string
        :return: Snapshot Id
        """
        # FIXME: if tag:Timestamp == latest, then flag = True
        flag = False
        tags = self.format_tags(tags)

        # FIXME: hard-coded string in tags
        if 'tag:Timestamp' in tags and \
                tags['tag:Timestamp'].lower() == 'latest':
            del tags['tag:Timestamp']
            flag = True

        snapshots = self.find_snapshot_by_tags(tags)
        if not snapshots:
            return None
        elif len(snapshots) > 1:
            # FIXME: hard-coded string in tags
            if not flag:
                return None
            snapshot = self.fetch_latest_snapshot(snapshots)
            if not snapshot:
                return None
            else:
                return snapshot.id
        else:
            return snapshots[0].id

    def clean_snapshots(self, tags, duration):
        """
        Clean up snapshots by specific tags and duration

        :type tags: dict
        :param tags: snapshot tags like

        .. code-block:: javascript

            {
              "Name": "XXX"
            }

        :type duration: int
        :param duration: seconds

        :rtype: list
        :return: list of cleaned snapshot ids
        """
        snapshots = self.find_snapshot_by_tags(self.format_tags(tags))
        deleted_ids = []
        for snapshot in snapshots:
            if 'Timestamp' in snapshot.tags:
                try:
                    tmp_time = strptime(snapshot.tags[
                                        'Timestamp'], "%Y%m%d-%H%M")
                    timestamp = mktime(tmp_time)
                except Exception, e:
                    log.error(e)
                    continue
                now = mktime(gmtime())
                if now - timestamp > duration:
                    deleted_ids.append(snapshot.id)
                    self.del_snapshot(snapshot.id)
        return deleted_ids

    def del_snapshot(self, snapshot_id):
        """
        Delete snapshots by snapshot_id

        :type snapshot_id: string
        :param snapshot_id: snapshot Id like 'snap-xxxxxx'

        :rtype: boolean
        :return: true, false, exception
        """
        return self.delete_snapshot(snapshot_id)

    def find_ami_by_tags(self, tags):
        """
        Find AMI by specific tags

        :type tags: dict
        :param tags: AMI tags like {'Name': 'XXX'}

        :rtype: list
        :return: list of boto image objects
        """
        return self.get_all_images(filters=self.format_tags(tags))

    def fetch_imageid_by_tags(self, **tags):
        """
        Fetch the Image Id by specific tags

        :type tags: dict
        :param tags: AMI tags like {'Name': 'XXX'}

        :rtype: string
        :return: Image Id
        """
        images = self.find_ami_by_tags(self.format_tags(tags))
        if not images:
            return None
        elif len(images) > 1:
            return None
        else:
            return images[0].id

    def get_all_zones(self):
        """
        Get all Availability Zones under this region

        :rtype: list
        :return: list of availability zones in this region
        """
        return [zone.name for zone in super(IcsEc2, self).get_all_zones()]

    def size_of_all_zones(self):
        """
        Get the number of all Availability Zones under this region

        :rtype: int
        :return: number of availability zones in this region
        """
        zone_list = self.get_all_zones()
        if zone_list:
            return len(zone_list)
        else:
            return 0

    def get_sgroup(self, name, vpc_id=None):
        """
        Get Security Group Name (if Ec2) / Id (if Vpc)

        :param name: security group name
        :type name: string

        :param vpc_id: vpc id
        :type vpc_id: string

        :rtype: string
        :return: security group id
        """

        if vpc_id is None:
            return name
        else:
            filters = {'vpc-id': vpc_id, 'group-name': name}

        group = self.get_all_security_groups(filters=filters)

        if group and isinstance(group, list):
            return group[0].id
        else:
            return None

    def get_security_group_id(self, name, vpc_id=None):
        """
        Get security group id

        :param name: security group name
        :type name: string

        :param vpc_id: vpc id
        :type vpc_id: string

        :rtype: string
        :return: security group id
        """

        if vpc_id:
            filters = {'vpc-id': vpc_id, 'group-name': name}
        else:
            filters = {'group-name': name}

        group = self.get_all_security_groups(filters=filters)

        if group:
            return group[0].id
        else:
            return None

    def get_az_from_subnet_id(self, subnet_id=None):
        """
        Get the name of Availability Zone by its Subnet Id

        :type subnet_id: string
        :param subnet_id: subnet id

        :rtype: string
        :return: availability zone name
        """
        if subnet_id is None:
            return self.get_all_zones()
        vpc = vpc_connect_to_region(self.region.name)
        subnets = vpc.get_all_subnets(subnet_id)
        if subnets and isinstance(subnets, list):
            return [subnets[0].availability_zone]
        else:
            return None

    def get_zone_name_for_cassandra(self, index):
        """
        Get the name of Availability Zone for Cassandra

        :type index: int
        :param index: the index of cassandra instance

        :rtype: string
        :return: zone name like "us-west-2a"
        """
        zone_list = self.get_all_zones()
        zone_size = self.size_of_all_zones()
        return zone_list[(int(index) - 1) % zone_size]

    def get_zone_index_for_cassandra(self, index):
        """
        Get the index of Availability Zone for Cassandra

        :type index: int
        :param index: the index of cassandra instance

        :rtype: string
        :return: zone index like "1"
        """
        zone_size = self.size_of_all_zones()
        return str((int(index) - 1) / zone_size + 1)

    def get_zone_suffix_for_cassandra(self, index):
        """
        Get the suffix of Availability Zone for Cassandra

        :type index: int
        :param index: the index of cassandra instance

        :rtype: string
        :return: zone suffix like "a-1"
        """
        return "-".join([self.get_zone_name_for_cassandra(index)[-1],
                        self.get_zone_index_for_cassandra(index)])




# vim: tabstop=4 shiftwidth=4 softtabstop=4
