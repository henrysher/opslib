"""
IcsSNS: Library for SNS
-----------------------

+--------------------+------------+--+
| This is the IcsSNS common library. |
+--------------------+------------+--+
"""

from boto import sns
from opslib.icsexception import IcsSNSException

import logging
log = logging.getLogger(__name__)


class IcsSNS(object):

    """
    ICS Libraray for SNS
    """

    def __init__(self, region, **kwargs):
        self.conn = sns.connect_to_region(region, **kwargs)

    def getTopicARN(self, name):
        """Get the ``Amazon Resource Name`` of specified SNS Topic

        :type name: str
        :param name: SNS Topic Name

        :rtype: string
        :return: a string containing ``Amazon Resource Name``
        """
        topics = self.conn.get_all_topics()
        arns = topics['ListTopicsResponse']['ListTopicsResult']['Topics']
        for a in arns:
            arn = a['TopicArn']
            if arn.split(':')[-1] == name:
                return arn
        return None

    def publish(self, topic_arn, msg, subj=None):
        """
        Publish messages to SNS Topic

        :type topic_arn: string
        :param topic_arn: ``Amazon Resource Name`` for SNS


        :type msg: string
        :param msg: message contents

        :type subj: string
        :param subj: subject contents
        """
        self.conn.publish(topic_arn, msg, subj)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
