#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from logging.config import dictConfig
import signal

from pybot.core import log

__author__ = 'Eric Pascual'

dictConfig(log.get_logging_configuration({
    'handlers': {
        'file': {
            'filename': '/tmp/youpinitel.log'
        }
    },
    'loggers': {
        'root': {
            'handlers': ['console']
        }
    }
}))


def main():
    terminate = False

    def catch_sigterm(*args):
        global terminate
        terminate = True

    signal.signal(signal.SIGTERM, catch_sigterm)

    logger = log.getLogger('youpinitel')

    while not terminate:
        logger.info('running...')
        time.sleep(0.5)

    logger.info('terminated by SIGTERM')
