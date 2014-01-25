"""
ICS Unit Test for Common Library
"""

import sys

# The unittest module got a significant overhaul
# in 2.7, so if we're in 2.6 we can use the backported
# version unittest2.
if sys.version_info[:2] == (2, 6):
    import unittest2 as unittest
else:
    import unittest

# vim: tabstop=4 shiftwidth=4 softtabstop=4
