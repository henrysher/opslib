"""
IcsSqs: Library for SQS
-----------------------

+--------------------+------------+--+
| This is the IcsSQS common library. |
+--------------------+------------+--+
"""

from boto.sqs import connect_to_region

import logging
log = logging.getLogger(__name__)


class IcsSqs(object):

    """
    ICS Library for SQS
    """

    def __init__(self, region, **kwargs):
        self.conn = connect_to_region(region)

    def create_queue(self, name, visibility_timeout=None):
        """
        Create an SQS Queue.

        :param name: The name of the new queue. \
             Names are scoped to an account and \
             need to be unique within that account.
        :type name: string

        :param visibility_timeout: The default visibility timeout for all \
             messages written in the queue.
        :type visibility_timeout: int

        :return: The newly created queue
        :type: boto.sqs.queue.Queue
        """

        return self.conn.create_queue(
            name,
            visibility_timeout=visibility_timeout)

    def get_queues(self, name=''):
        """
        If name is empty, it will get all queues, else it retrieves the queue
        with the given name.

        :param name: The name of the queue to retrieve.
        :type name: string

        :return: The requested queue(list of queues), \
            or None if no match was found
        :type: boto.sqs.queue.Queue or None or \
            list of boto.sqs.queue.Queue instances
        """

        if name:
            return self.conn.get_queue(name)
        else:
            return self.conn.get_all_queues()

    def delete_queue(self, name):
        """
        Delete the queue

        :param name: According to the given name to delete the queue
        :type name: string

        :return: The result of this action
        :type: bool
        """

        sqs = self.get_queues(name)
        if sqs:
            return sqs.delete()
