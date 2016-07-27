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


class GracefulKiller(object):
    kill_now = False

    def __init__(self, logger):
        self.logger = logger
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.logger.info("signal %d caught", signum)
        self.kill_now = True


def main():
    logger = log.getLogger('youpinitel')
    killer = GracefulKiller(logger)

    while not killer.kill_now:
        logger.info('running...')
        time.sleep(0.5)

    logger.info('terminated')
