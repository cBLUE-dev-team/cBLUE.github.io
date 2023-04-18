"""
Summary:    This file contains the custom logging functionality.
Author:     Forrest Corcoran
Date:       5/20/2022

Last Edited by: Keana Kief
Last Edited: April 11th, 2023
"""
import logging


class CustomLogger:
    """
    class: CustomLogger
    ------

    Description: This is a utility class to add custom logging to CBLUE.
    ------------ The CustomLogger class is called at the top of __main__
                 (i.e. CBlue.py), and the logger is accessed at each
                 submodule using `logger = logging.getLogger(__name__).
                 Logging levels are defined for each submodule of CBLUE
                 and can be further extended by modifying _LOGGER_LEVELS.
                 Note that some levels (10,20,30,...) are already defined
                 by the logging library and should not be overwritten.
                 Also note that each level is accessed through
                 logging.new_level("some message"), where new_level is
                 strictly lowercase.

    Parents: None
    --------

    Args: None
    -----

    Kwargs: (str) filename - the path to the log file (will be created if
    -------                  it doesn't already exist). File is overwritten
                             on each run. Default = None (i.e. log to terminal).
    """

    _LOGGER_LEVELS = {
        "CBlue": 21,
        "Tpu": 22,
        "Subaerial": 23,
        "Subaqueous": 24,
        "SBet": 25,
        "Las": 26,
        "Merge": 27,
        "Datum": 28,
        "LasGrid": 29,
        "Sensor": 31
    }

    def __init__(self, filename=None):
        # configure log file
        logging.basicConfig(
            filename=filename,
            format="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.NOTSET,  # NOTSET logs all log levels
            filemode="w",  # overwrite log file each time
        )

        # add log functions to logging library from _LOGGER_LEVELS
        for levelName, levelNum in CustomLogger._LOGGER_LEVELS.items():
            addLoggingLevel(levelName.upper(), levelNum)


def addLoggingLevel(levelName, levelNum):
    """
    This is a friend function of CustomLogger that is used to modify
    the loggging library with the desired levels (defined in
    CustomLogger._LOGGER_LEVELS).
    """

    methodName = levelName.lower()

    # check if the new level is already defined somewhere
    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))

    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))

    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # logs submodule messages
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    # logs root messages
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    # give logging library the new name and level
    logging.addLevelName(levelNum, levelName)

    # set functionality of the new level
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)
