import logging

logging.basicConfig(level=level)


def debug(msg):
    logging.debug(msg)


def info(msg):
    logging.info(msg)


def warn(msg):
    logging.warning(msg)


def error(msg):
    logging.error(msg)


def exception(msg, *args, **kwargs):
    logging.exception(msg, *args, **kwargs)
