"""
IcsAS: Library for Auto Scaling
-------------------------------

+--------------------+------------+--+
| This is the IcsAS common library.  |
+--------------------+------------+--+
"""

from boto.ec2.autoscale import regions
from boto.ec2.autoscale import AutoScaleConnection
from opslib.icsutils.misc import dict_merge
from opslib.icsutils.misc import gen_timestamp
from opslib.icsutils.misc import user_data_decode
from opslib.icsutils.misc import clean_empty_items
from opslib.icsutils.misc import init_botocore_service, operate
from opslib.icsutils.misc import filter_resource_from_json
from opslib.icsutils.misc import keyname_formatd
from opslib.icsutils.misc import fetch_used_params
from opslib.icsexception import IcsASException

import logging
log = logging.getLogger(__name__)


def get_region(region_name, **kw_params):
    """
    Find and return a :class:`boto.ec2.autoscale.RegionInfo` object
    given a region name.

    :type region_name: str
    :param region_name: The name of the region.

    :rtype: :class:`boto.ec2.autoscale.RegionInfo`
    :return: The RegionInfo object for the given region or None if
             an invalid region name is provided.
    """
    for region in regions(**kw_params):
        if region.name == region_name:
            return region
    return None


class IcsAS(object):

    """
    ICS Library for AutoScale
    """

    def __init__(self, region, **kwargs):
        self.conn = AutoScaleConnection(region=get_region(region), **kwargs)

    def to_list(self, input):
        """
        Validate input, if not list, but string, make it as a list
        """
        if input is None:
            return input
        elif isinstance(input, list):
            return input
        elif isinstance(input, basestring):
            return [input]
        else:
            raise IcsASException("Need the type '%s' but '%s' found"
                                 % ('list', type(input)))

    def get_group_name_from_instance(self, instance_id):
        """
        Get the ASG name from the specific instance id

        :type instance_id: string
        :param instance_id: EC2 instance id startwith 'i-xxxxxxx'

        :rtype: string
        :return: name of the ASG, this instance belongs to
        """
        instances = self.conn.get_all_autoscaling_instances(
            instance_ids=self.to_list(instance_id))
        if instances:
            return instances[0].group_name
        else:
            return None

    def get_instances_from_group_name(self, name):
        """
        Get the instance from the specific ASG name

        :type name: string
        :param name: the specific ASG name

        :rtype: list
        :return: a list contains all the instances
        """
        instances = []
        for group in self.conn.get_all_groups(names=self.to_list(name)):
            instances.extend(group.instances)
        return instances

    def get_group_from_name(self, name):
        """
        Get the ASG from its name

        :type name: string
        :param name: the ASG name

        :rtype: list
        :return: a list represents the specific ASG(s)
        """
        return self.conn.get_all_groups(names=self.to_list(name))

    def get_launch_config_from_name(self, name):
        """
        Get the Launch Configuration from its name

        :type name: string
        :param name: the Launch Configuration name

        :rtype: list
        :return: a list represents the specific Launch Configuration(s)
        """
        return self.conn.get_all_launch_configurations(
            names=self.to_list(name))

    def create_launch_config(self, launch_config):
        """
        Create the Launch Configuration

        :type launch_config: class
        :param launch_config: boto launch_config object

        :rtype: string
        :return: AWS request Id
        """
        return self.conn.create_launch_configuration(launch_config)

    def delete_launch_config_from_name(self, name):
        """
        Delete the Launch Configuration from its name

        :type name: string
        :param name: the name of launch configuration

        :rtype: string
        :return: AWS request Id
        """
        return self.conn.delete_launch_configuration(name)

    def update_launch_config(self, name, launch_config):
        """
        Update the Launch Configuration for specific ASG

        :type name: string
        :param name: the name of Auto-Scaling Group

        :type launch_config: class
        :param launch_config: boto launch_config object

        :rtype: string
        :return: AWS request Id
        """
        groups = self.get_group_from_name(name)
        if groups:
            group = groups[0]
        else:
            raise IcsASException("no such Auto-Scaling Group '%s' found"
                                 % name)

        self.create_launch_config(launch_config)
        old_lc_name = group.launch_config_name
        new_lc_name = launch_config.name
        group.__dict__["launch_config_name"] = launch_config.name
        group.update()

        if self.get_launch_config_from_name(new_lc_name):
            group = self.get_group_from_name(name)[0]
            if group.launch_config_name == new_lc_name:
                return self.delete_launch_config_from_name(old_lc_name)
            else:
                raise IcsASException("Failed to update " +
                                     "launch config for ASG '%s'"
                                     % name)
        else:
            raise IcsASException("no such new launch config '%s'"
                                 % new_lc_name)

    def suspend_scaling_group(self, name, scaling_processes=None):
        """
        Suspends Auto Scaling processes for an Auto Scaling group.

        :type name: string
        :param name: the ASG name

        :type scaling_processes: string or list
        :param scaling_processes: scaling process names

         * Launch
         * Terminate
         * HealthCheck
         * ReplaceUnhealthy
         * AZRebalance
         * AlarmNotification
         * ScheduledActions
         * AddToLoadBalancer
        """
        if not isinstance(name, basestring):
            return None
        group = self.get_group_from_name(self.to_list(name))[0]
        return group.suspend_processes(self.to_list(scaling_processes))

    def resume_scaling_group(self, name, scaling_processes=None):
        """
        Resumes Auto Scaling processes for an Auto Scaling group.

        :type name: string
        :param name: the ASG name

        :type scaling_processes: string or list
        :param scaling_processes: scaling process names

         * Launch
         * Terminate
         * HealthCheck
         * ReplaceUnhealthy
         * AZRebalance
         * AlarmNotification
         * ScheduledActions
         * AddToLoadBalancer
        """
        if not isinstance(name, basestring):
            return None
        group = self.get_group_from_name(self.to_list(name))[0]
        return group.resume_processes(self.to_list(scaling_processes))

    def terminate_group_instance(self, instance_id, decrement_capacity=True):
        """
        Terminates the specified instance. The desired group size can
        also be adjusted, if desired.

        :type instance_id: str
        :param instance_id: The ID of the instance to be terminated.

        :type decrement_capability: bool
        :param decrement_capacity: Whether to decrement the size of the
            autoscaling group or not.
        """
        return self.conn.terminate_instance(
            instance_id=instance_id,
            decrement_capacity=decrement_capacity)

    def update_instance_health(self, instance_id, health_status,
                               grace_period=False):
        """
        Explicitly set the health status of an instance.

        :type instance_id: str
        :param instance_id: The identifier of the EC2 instance

        :type health_status: str
        :param health_status: The health status of the instance.

        * Healthy: the instance is healthy and should remain in service.
        * Unhealthy: the instance is unhealthy. \
            Auto Scaling should terminate and replace it.

        :type grace_period: bool
        :param grace_period: If True, this call should respect
            the grace period associated with the group.
        """

        self.conn.set_instance_health(instance_id, health_status,
                                      should_respect_grace_period=grace_period)


class RawAS(object):

    """
    Raw Library for AutoScale, based on Botocore
    """

    def __init__(self, region):
        """
        Initialize the proper botocore service
        """
        self.name = "autoscaling"
        self.region = region
        self.service, self.endpoint = init_botocore_service(
            self.name, self.region)

    def fetch_all_groups(self):
        """
        Fetch all the Auto-Scaling Groups

        :rtype: dict
        :return: JSON object for all the Auto-Scaling Groups
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DescribeAutoScalingGroups"
        return operate(self.service, cmd, endpoint)

    def find_groups(self, filter={}):
        """
        Find the names of Auto-Scaling Groups in the filters

        :type filter: dict
        :param filter: a dictionary to used for resource filtering
            The format should be consistent with botocore JSON output

        .. code-block:: javascript

            {
              "Tags": [
                {
                  "Key": "Owner",
                  "Value": "Production"
                }
              ]
            }

        :rtype: list
        :return: a list containing all the names of filtered groups
        """
        names = ["AutoScalingGroupName", "LaunchConfigurationName"]
        status, raw_data = self.fetch_all_groups()
        return filter_resource_from_json(names, filter=filter,
                                         raw_data=raw_data)

    def handle_response(self, response):
        """
        Handle the botocore response
        """
        if response[0].status_code == 200:
            return response[0].reason, response[1]
        raise IcsASException("Status Code: %s; Reason: %s" % (
            response[0].status_code, response[0].reason))

    def fetch_group(self, name):
        """
        Fetch an existing Auto-Scaling Group

        :type name: string
        :param name: auto-scaling group name
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DescribeAutoScalingGroups"
        key = 'AutoScalingGroupNames'
        params = {key: [name]}
        params = keyname_formatd(params)
        params.update(endpoint)
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)

        result, data = self.handle_response(response)
        groups = data['AutoScalingGroups']
        if not groups:
            raise IcsASException(
                "auto-scaling group '%s': not found" % name)
        elif len(groups) > 1:
            raise IcsASException(
                "too many auto-scaling groups found: '%s'" % group)
        return groups[0]

    def fetch_launch_config(self, name):
        """
        Fetch an existing Launch Configuration

        :type name: string
        :param name: launch configuration name
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DescribeLaunchConfigurations"
        key = 'LaunchConfigurationNames'
        params = {key: [name]}
        params = keyname_formatd(params)
        params.update(endpoint)

        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)

        result, data = self.handle_response(response)
        lcs = data['LaunchConfigurations']
        if not lcs:
            raise IcsASException(
                "auto-scaling group '%s': not found" % name)
        elif len(lcs) > 1:
            raise IcsASException(
                "too many auto-scaling groups found: '%s'" % lcs)
        return lcs[0]

    def create_group(self, group_config):
        """
        Create a new Auto-Scaling Group

        :type group_config: dict
        :param group_config: auto-scaling group configuration
        """
        endpoint = {'endpoint': self.endpoint}
        params = keyname_formatd(group_config)
        params.update(endpoint)
        cmd = "CreateAutoScalingGroup"
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def create_launch_config(self, launch_config):
        """
        Create a new Launch Configuration

        :type launch_config: dict
        :param launch_config: launch configuration
        """
        endpoint = {'endpoint': self.endpoint}
        params = keyname_formatd(launch_config)
        params.update(endpoint)
        cmd = "CreateLaunchConfiguration"
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def delete_group(self, name):
        """
        Delete an existing Auto-Scaling Group

        :type name: string
        :param name: auto-scaling group name
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DeleteAutoScalingGroup"
        key = 'AutoScalingGroupName'
        params = {key: name}
        params['ForceDelete'] = True
        params = keyname_formatd(params)
        params.update(endpoint)
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def delete_launch_config(self, name):
        """
        Delete an existing Launch Configuration

        :type name: string
        :param name: launch configuration name
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DeleteLaunchConfiguration"
        key = 'LaunchConfigurationName'
        params = {key: name}
        params = keyname_formatd(params)
        params.update(endpoint)
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def modify_launch_config(self, launch_config, delimiter='_U_'):
        """
        Modify the Launch Configuration

        :type launch_config: dict
        :param launch_config: launch configuration
        """
        lc_name = launch_config['LaunchConfigurationName']
        if delimiter in lc_name:
            new_lc_name = delimiter.join([lc_name.split(
                delimiter)[0], gen_timestamp()])
        else:
            new_lc_name = delimiter.join([lc_name, gen_timestamp()])
        launch_config['LaunchConfigurationName'] = new_lc_name
        self.create_launch_config(launch_config)
        return new_lc_name

    def modify_group(self, group_config):
        """
        Modify the Auto-Scaling Group

        :type group_config: dict
        :param group_config: auto-scaling group configuration
        """
        endpoint = {'endpoint': self.endpoint}
        params = keyname_formatd(group_config)
        params.update(endpoint)
        cmd = "UpdateAutoScalingGroup"
        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def update_group(self, group_config, launch_config):
        """
        Update the Auto-Scaling Group

        :type group_config: dict
        :param group_config: auto-scaling group configuration

        :type launch_config: dict
        :param launch_config: launch configuration
        """
        group_name = group_config['AutoScalingGroupName']
        group_data = clean_empty_items(self.fetch_group(group_name))
        lc_name = group_data['LaunchConfigurationName']
        launch_data = clean_empty_items(self.fetch_launch_config(lc_name))

        launch_config = dict_merge(launch_data, launch_config)

        # FIXME: need to refine and remove the unused items
        user_data = launch_config['UserData']
        launch_config['UserData'] = user_data_decode(user_data)
        if 'CreatedTime' in launch_config:
            launch_config.pop('CreatedTime')
        if 'LaunchConfigurationARN' in launch_config:
            launch_config.pop('LaunchConfigurationARN')

        if launch_config == launch_data:
            log.info("no need to update the launch configuration")
        else:
            log.info("update the launch configuration")
            new_lc_name = self.modify_launch_config(launch_config)
            group_config['LaunchConfigurationName'] = new_lc_name
            log.info("New launch configuration name:")
            log.info(">> %s" % new_lc_name)

        log.info("update the auto-scaling group")
        try:
            log.info(self.modify_group(group_config))
        except Exception, e:
            log.error(e)
            log.info("delete the new launch configuration:")
            log.info(">> %s" % new_lc_name)
            return self.delete_launch_config(new_lc_name)
        else:
            log.info("delete the old launch configuration:")
            log.info(">> %s" % lc_name)
            return self.delete_launch_config(lc_name)

    def launch_group(self, group_config, launch_config):
        """
        Launch a new Auto-Scaling Group

        :type group_config: dict
        :param group_config: auto-scaling group configuration

        :type launch_config: dict
        :param launch_config: launch configuration
        """
        result = {}
        try:
            response = self.create_launch_config(launch_config)
        except Exception, e:
            log.error(e)
        else:
            result['CreateLaunchConfiguration'] = response
        try:
            response = self.create_group(group_config)
        except Exception, e:
            log.error(e)
        else:
            result['CreateAutoScalingGroup'] = response
        return result

    def kill_group(self, group_name, force=False):
        """
        Delete a new Auto-Scaling Group

        :type name: string
        :param name: launch configuration name

        :type force: boolean
        :param force: whether to delete the auto-scaling group forcely
        """
        try:
            group_data = self.fetch_group(group_name)
        except Exception, e:
            return e
        lc_name = group_data['LaunchConfigurationName']
        if group_data['Instances'] and not force:
            error_msg = "auto-scaling group '%s' " % group_name + \
                "has running instances, " + \
                "if you have to kill it forcely, " + \
                "please use '-force'"
            return error_msg

        result = {}
        try:
            response = self.delete_group(group_name)
        except Exception, e:
            log.error(e)
        else:
            result['DeleteAutoScalingGroup'] = response
        try:
            response = self.delete_launch_config(lc_name)
        except Exception, e:
            log.error(e)
        else:
            result['DeleteLaunchConfiguration'] = response
        return result

    def new_scaling_policy(self, scaling_policy, metric_alarm):
        """
        Create a new Scaling Policy

        :type scaling_policy: dict
        :param scaling_policy: scaling policy configuration

        :type metric_alarm: dict
        :param metric_alarm: metric alarm configuration
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "PutScalingPolicy"
        params = fetch_used_params(self.name, cmd, scaling_policy)
        params.update(endpoint)

        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            log.error("Failed to create this scaling policy...")
            raise IcsASException(e)
        policy_arn = self.handle_response(response)[1]['PolicyARN']

        # FIXME: special here, just for cloudwatch service
        name = "cloudwatch"
        service, endpoint = init_botocore_service(name, self.region)
        endpoint = {'endpoint': endpoint}
        cmd = "PutMetricAlarm"
        metric_alarm['AlarmActions'].append(policy_arn)
        params = fetch_used_params(name, cmd, metric_alarm)
        params.update(endpoint)
        try:
            response = operate(service, cmd, params)
        except Exception, e:
            log.error("Failed to create this metric alarm...")
            raise IcsASException(e)
        return self.handle_response(response)[0]

    def delete_scaling_policy(self, scaling_policy, metric_alarm):
        """
        Delete an existing Scaling Policy

        :type scaling_policy: dict
        :param scaling_policy: scaling policy configuration

        :type metric_alarm: dict
        :param metric_alarm: metric alarm configuration
        """
        endpoint = {'endpoint': self.endpoint}
        cmd = "DeletePolicy"
        params = fetch_used_params(self.name, cmd, scaling_policy)
        params.update(endpoint)

        try:
            response = operate(self.service, cmd, params)
        except Exception, e:
            log.error("Failed to delete this scaling policy...")
            log.error(e)

        # FIXME: special here, just for cloudwatch service
        name = "cloudwatch"
        service, endpoint = init_botocore_service(name, self.region)
        endpoint = {'endpoint': endpoint}
        cmd = "DeleteAlarms"
        metric_alarm['AlarmNames'] = [metric_alarm['AlarmName']]
        params = fetch_used_params(name, cmd, metric_alarm)
        params.update(endpoint)

        try:
            response = operate(service, cmd, params)
        except Exception, e:
            log.error("Failed to delete this metric alarm...")
            raise IcsASException(e)
        return self.handle_response(response)[0]

# vim: tabstop=4 shiftwidth=4 softtabstop=4
