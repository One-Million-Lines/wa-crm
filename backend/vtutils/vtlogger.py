"""
Module used to configure and intialize the logging facility.
Outputs to stdout/stderr.
initLog needs to be called once per application.

Example usage:
Main module:
vtLog = VTLogger.initLog("my_app")
vtLog.debug("test")
vtLog.info("reached checkpoint")
vtLog.error("Kaboom")

Subsequent modules:
!!!Important: For this to work, you must ensure that the "getLog" util
is called AFTER the "initLog" util!!!
vtLog = getLog("my_module") #Can be used at module level
                        # Will be displayed as myapp.my_module
vtLog.error("Error!")
"""

from sys import stdout, stderr

import logging
import logging.handlers
import json
from logging import Logger
import traceback
import datetime
from vtutils.misc import make_dict_json_serializable

from vtutils.misc import decode_bytes_value

LOGGER_NAME = "main"
FILTERS = []

class VTLogger(Logger):

    def __init__(self, name):
        super(VTLogger, self).__init__(name)

    def remove_curly (self, msg):
        """
        remove first and last characters of a string if they are curly brackets
        """
        if msg and msg.startswith("{"):
            msg = msg[1:]
        if msg and msg.endswith("}"):
            msg = msg[:-1]
        return msg
    def format_msg(self, msg, *args, **kwargs):
        """
        formats log object
        """
        log_object = {}
        try:
            if msg and isinstance(msg, str):
                #log_object["msg"] = msg.encode('utf-8')
                log_object["msg"] = msg
            passed_kwargs = {}
            if kwargs:
                #before using simplejson this was not converting keys right
                #kwargs = decode_dict_bytes(kwargs)
                # here we can loop through kwargs and if keys end with _id we make them integer
                for item in kwargs:
                    if item.endswith("_id") and isinstance(kwargs[item], str) and kwargs[item].isdigit():
                        kwargs[item] = int(kwargs[item])
                # those keys get removed from kwargs
                if "exc_info" in kwargs:
                    passed_kwargs["exc_info"] = kwargs.pop("exc_info")
                if "extra" in kwargs:
                    passed_kwargs["extra"] = kwargs.pop("extra")
                kwargs = make_dict_json_serializable(kwargs)
                #logs get updated with kwargs dict
                log_object.update(kwargs)
            return log_object, passed_kwargs
        except Exception as e:
            self.error("Error formating log msg " + (msg if isinstance(msg, str) else '') + str(e))
            return {},{}

    def debug(self, _msg, *args, **kwargs):
        log_object, passed_kwargs = self.format_msg(_msg, *args, **kwargs)
        # json_dumps might generate itself errors
        super(VTLogger, self).debug(
            self.remove_curly(json.dumps(log_object)), *args, **passed_kwargs)

    def info(self, _msg, *args, **kwargs):
        log_object, passed_kwargs = self.format_msg(_msg, *args, **kwargs)
        # json_dumps might generate itself errors
        super(VTLogger, self).info(
            self.remove_curly(json.dumps(log_object)), *args, **passed_kwargs)

    def warning(self, _msg, *args, **kwargs):
        log_object, passed_kwargs = self.format_msg(_msg, *args, **kwargs)
        super(VTLogger, self).warning(
            self.remove_curly(json.dumps(log_object)), *args, **passed_kwargs)

    # alias so warn() also works with kwargs
    # warn = warning

    def error(self, _msg, *args, **kwargs):
        log_object, passed_kwargs = self.format_msg(_msg, *args, **kwargs)
        # if exc in message it automatically gets and sends traceback
        if "exc" not in log_object:
            log_object["err_type"] = "custom"
        else:
            log_object["err_type"] = type(log_object["exc"]).__name__
            log_object["err_details"] = repr(log_object["exc"])
            log_object["traceback"] = traceback.format_exc()
            del log_object["exc"]
        try:
            super(VTLogger, self).error(
                self.remove_curly(json.dumps(log_object)), *args, **passed_kwargs)
        except Exception as e:
            self.error("error_format_log", original_msg=repr(log_object), exc=e)

class AppFilter(logging.Filter):
    def __init__(self, hostname=None, proc_id=None):
        super(AppFilter, self).__init__()
        self._hostname = hostname
        self._proc_id = proc_id

    def filter(self, record):
        record.host = self._hostname
        record.proc_id = self._proc_id
        return True


class VT4Formatter(logging.Formatter):
    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        t = ct.strftime("%Y-%m-%dT%H:%M:%S")
        s = "%s.%03d" % (t, record.msecs)
        return s


def _has_matching_filter(logger, host, proc_id):
    for existing_filter in logger.filters:
        if not isinstance(existing_filter, AppFilter):
            continue
        if existing_filter._hostname == host and existing_filter._proc_id == proc_id:
            return True
    return False


def _has_stdout_handler(logger):
    for handler in logger.handlers:
        if getattr(handler, "_vtlogger_stdout", False):
            return True
    return False


def initLog(logger_name, default_level="debug", host="localhost", proc_id=0):
    """
    Initalizes the logging facility. Can be called just
    once by the application.

    Args:
        logger_name (str): root path for logging messages.
        default_level (str, optional): debugging level used. Can be
            'debug', 'info' or 'error'.

    Returns:
        logger: logger object.
    """
    logging.setLoggerClass(VTLogger)
    debug_levels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "error": logging.ERROR
    }
    logger = logging.getLogger(logger_name)
    logger.setLevel(debug_levels[default_level])

    already_initialized = _has_stdout_handler(logger)

    debug_fh = logging.StreamHandler(stream=stdout)
    error_fh = logging.StreamHandler(stream=stderr)

    filter = AppFilter(hostname=host, proc_id=proc_id)
    if not _has_matching_filter(logger, host, proc_id):
        logger.addFilter(filter)
    global FILTERS
    FILTERS = logger.filters
    debug_fh.setLevel(logging.DEBUG)
    error_fh.setLevel(logging.ERROR)
    # removed "host": "%(host)s",
    std_formatter = VT4Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s",' +
        ' "name": "%(name)s-%(proc_id)s", %(message)s}')
    # error_formatter = logging.Formatter(
    #     '{"timestamp": "%(asctime)s", "level": "%(levelname)s",' +
    #     ' "module": "%(name)s", %(message)s}')

    debug_fh.setFormatter(std_formatter)
    error_fh.setFormatter(std_formatter)

    if not already_initialized:
        debug_fh._vtlogger_stdout = True
        logger.addHandler(debug_fh)
    # logger.addHandler(error_fh)
    logger.propagate = False

    if not already_initialized:
        logger.info("Logging initialized")
    global LOGGER_NAME
    LOGGER_NAME = logger_name if logger_name != "tornado" else LOGGER_NAME
    return logger


# initLog("tornado")

"""
return existing log 
"""
def getLog(existing_log_name=""):
    logger = None
    if LOGGER_NAME != "" and existing_log_name:
        logger = logging.getLogger("{0}.{1}".format(LOGGER_NAME, existing_log_name))
        for filter in FILTERS:
            if filter not in logger.filters:
                logger.addFilter(filter)
    elif LOGGER_NAME and not existing_log_name:
        logger = logging.getLogger(LOGGER_NAME)
    else:
        logger = logging.getLogger(existing_log_name)
    return logger
