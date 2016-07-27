#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from logging.config import dictConfig

from pybot.core import log

from pybot.youpi2.apps.utils import GracefulKiller

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
    logger = log.getLogger('youpinitel')
    killer = GracefulKiller(logger)

    while not killer.kill_now:
        logger.info('running...')
        time.sleep(0.5)

    logger.info('terminated')
