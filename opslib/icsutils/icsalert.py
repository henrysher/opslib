"""
IcsAlert: Library for Alert
---------------------------

+------------------------+-------------+
| This is the IcsAlert common library. |
+------------------------+-------------+
"""

from time import strftime
from time import gmtime

from opslib.icssns import IcsSNS
from opslib.icsexception import IcsAlertException

import logging
log = logging.getLogger(__name__)


class IcsAlert(object):
    def __init__(self, region, topic, msg_prefix="", **kwargs):
        """Generate and send alerts when exceptions occur

        :type region: str
        :param region: indicate region name you need to generate
            SNS alerts

        :type topic: str
        :param topic: indicate topic name you have already setup
            in SNS

        :type msg_prefix: str
        :param msg_prefix: prefix of alert message

        """
        self.region = region
        self.sns = IcsSNS(region, **kwargs)
        self.arn = self.sns.getTopicARN(topic)
        if self.arn is None:
            raise IcsAlertException("Cannot find topic: '%s'" % (topic))
        self.msg_prefix = msg_prefix

    def sendAlert(self, msg, subj_result):
        """
        Send SNS message as an Alert

        :type msg: str
        :param msg: message of the alert

        :type subj_result: str
        :param subj_result: SUCCESS/ERROR described in subject content
        """
        ts = strftime("%Y-%m-%d %H:%M:%S UTC", gmtime())
        subj = "[%s] %s" % (subj_result, self.msg_prefix)
        msg = "[%s] [%s]: %s" % (ts, self.msg_prefix, msg)
        self.sns.publish(self.arn, msg, subj)

    def sendHealthAlert(self, msg, subj):
        """
        Send SNS message as an Alert

        :type msg: str
        :param msg: message of the alert

        :type subj: str
        :param subj: subject of message
        """

        self.sns.publish(self.arn, msg, subj)

# vim: tabstop=4 shiftwidth=4 softtabstop=4
