# -*- coding: utf-8 -*-
import signal

__author__ = 'Eric Pascual'


class GracefulKiller(object):
    kill_now = False

    def __init__(self, logger):
        self.logger = logger
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.logger.info("signal %d caught", signum)
        self.kill_now = True