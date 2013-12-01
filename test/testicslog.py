#!/usr/local/bin/python

from icslog import IcsLog
import sys


def test_1():
    test_logger_1 = IcsLog("test_1", 1)                                      #Only ouput to the console
    test_logger_1.debug("Just for debug test %s", "test case 1")

def test_2():
    test_logger_2 = IcsLog("test_2", 0, "/etc/iscan/test.log")               #Only output to the log file /etc/iscan/test.log'''
    test_logger_2.info("%s\tJust for debug test %s", __file__, "test case 2")

def test_3():
    test_logger_3 = IcsLog("test_3", 1, "/etc/iscan/test.log")               #Output to the console and  the log file /etc/iscan/test.log
    test_logger_3.set_error_level()                                #Logging messages which are less severe than error will be ignored.
    test_logger_3.debug("Just for warning test %s", "test case 3")
    test_logger_3.info("Just for warning test %s", "test case 3")
    test_logger_3.warning("Just for warning test %s", "test case 3")
    test_logger_3.critical ("Just for warning test %s", "test case 3")
    test_logger_3.error("%s\t%s\t%d\tJust for debug test", sys._getframe().f_code.co_filename, sys._getframe().f_code.co_name, sys._getframe().f_lineno)

def main():
    test_1()
    test_2()
    test_3()

if __name__ == "__main__":
    main()
