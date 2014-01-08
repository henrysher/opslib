"""
IcsException: Library for Exception
-----------------------------------

+-----------------+------------+-----------+
| This is the IcsException common library. |
+-----------------+------------+-----------+
"""


class IcsException(Exception):

    """
    Error for ics exception
    """


class IcsAlertException(IcsException):

    """
    Error generating or sending alerts
    """


class IcsEc2Exception(IcsException):

    """
    Error for EC2 request
    """


class IcsASException(IcsException):

    """
    Error for Autoscale request
    """


class IcsMetaException(IcsException):

    """
    Error for ICS Meta process
    """


class IcsR53Exception(IcsException):

    """
    Errors processing ICS R53 request
    """


class IcsS3Exception(IcsException):

    """
    Errors processing ICS S3 request
    """


class IcsSNSException(IcsException):

    """
    Errors processing ICS SNS request
    """


class IcsSysCfgException(IcsException):

    """
    Errors for ICS System Configuration
    """

# vim: tabstop=4 shiftwidth=4 softtabstop=4
