"""
IcsLog: Library for Log
-----------------------

+--------------------+---------------+
| This is the IcsLog common library. |
+--------------------+---------------+
"""

import logging
import fcntl
import time
from logging.handlers import RotatingFileHandler


class NullHandler(logging.Handler):

    def emit(self, record):
        pass


class IcsLog(object):

    """
    ICS Log Library
    """

    def __init__(self, name, console=True, logfile=None, level="DEBUG"):
        """
        Initialize the Ics Log

        :type name: string
        :param name: the logger name, \
            this param should be different for different loggers

        :type console: int
        :param console: whether output the log to the console, \
            value should be 0 or 1

        :type logfile: string
        :param logfile: the file to save the logs

        :rtype: class object
        :return: a log object
        """
        self._level = getattr(logging, level.upper())

        self._mode = "a"
        self._max_bytes = 10 * 1024 * 1024
        self._rotate_count = 5
        self._log_file = logfile
        self._console = console
        self._lock_file = None
        self._fp = None
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self._level)

        # logging.Formatter.converter = time.gmtime
        formatter = logging.Formatter(
            "%(asctime)s\t%(levelname)s\t%(message)s", "%Y-%m-%d %H:%M:%S %Z")

        if not self._console and self._log_file is None:
            self._logger.addHandler(NullHandler())

        if self._console:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self._logger.addHandler(stream_handler)

        if self._log_file is not None:
            self._lock_file = logfile + ".lock"

            rotate_handler = RotatingFileHandler(
                filename=self._log_file,
                mode=self._mode,
                maxBytes=self._max_bytes,
                backupCount=self._rotate_count)
            rotate_handler.setFormatter(formatter)
            self._logger.addHandler(rotate_handler)

    def set_debug_level(self):
        """
        Sets the threshold for this logger to debug.
        Logging messages will all be printed.
        """

        if self._logger is not None:
            self._logger.setLevel(logging.DEBUG)

    def set_info_level(self):
        """
        Sets the threshold for this logger to info.
        Logging messages which are less severe than info will be ignored.
        """

        if self._logger is not None:
            self._logger.setLevel(logging.INFO)

    def set_warning_level(self):
        """
        Sets the threshold for this logger to warning.
        Logging messages which are less severe than warning will be ignored.
        """

        if self._logger is not None:
            self._logger.setLevel(logging.WARNING)

    def set_error_level(self):
        """
        Sets the threshold for this logger to error.
        Logging messages which are less severe than error will be ignored.
        """

        if self._logger is not None:
            self._logger.setLevel(logging.ERROR)

    def set_critical_level(self):
        """
        Sets the threshold for this logger to critical.
        Logging messages which are less severe than critical will be ignored.
        """

        if self._logger is not None:
            self._logger.setLevel(logging.CRITICAL)

    def _lock(self):
        """
        Lock the file
        """
        if self._lock_file is not None:
            self._fp = open(self._lock_file, 'w')
            if self._fp is not None:
                fcntl.flock(self._fp, fcntl.LOCK_EX)

    def _unlock(self):
        """
        Unlock the file
        """

        if self._fp is not None:
            fcntl.flock(self._fp, fcntl.LOCK_UN)
            self._fp.close()

    def debug(self, msg, *args, **kwargs):
        """
        Logs a message with level DEBUG on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.debug(msg, *args, **kwargs)
            self._unlock()

    def info(self, msg, *args, **kwargs):
        """
        Logs a message with level info on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.info(msg, *args, **kwargs)
            self._unlock()

    def warning(self, msg, *args, **kwargs):
        """
        Logs a message with level warning on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.warning(msg, *args, **kwargs)
            self._unlock()

    def error(self, msg, *args, **kwargs):
        """
        Logs a message with level error on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.error(msg, *args, **kwargs)
            self._unlock()

    def critical(self, msg, *args, **kwargs):
        """
        Logs a message with level critical on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.critical(msg, *args, **kwargs)
            self._unlock()

    def exception(self, msg, *args, **kwargs):
        """
        Logs a message with level exception on this logger.

        :type msg: string
        :param msg: message format string

        :type args: arguments
        :param args: the arguments which are merged into msg \
            using the string formatting operator

        :type kwargs: not recommended to use
        :param kwargs: not recommended to use
        """

        if self._logger is not None:
            self._lock()
            self._logger.exception(msg, *args, **kwargs)
            self._unlock()


# vim: tabstop=4 shiftwidth=4 softtabstop=4
