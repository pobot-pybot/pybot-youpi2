#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from logging.config import dictConfig

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
    logger = log.getLogger('youpinitel')
    while True:
        logger.info('running...')
        time.sleep(0.5)
