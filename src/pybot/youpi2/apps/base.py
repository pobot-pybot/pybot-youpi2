# -*- coding: utf-8 -*-

import time
import threading

from pybot.core import log

__author__ = 'Eric Pascual'


class Application(object):
    def __init__(self, arm, panel, logger):
        self.arm = arm
        self.panel = panel
        self.logger = logger or log.getLogger(name=self.__class__.__name__)

        self._terminated = False
        self._worker = None

    def start(self):
        if self._worker:
            raise ApplicationError('already running')

        self._worker = threading.Thread(name=self.__class__.__name__ + '.worker', target=self._worker_loop)
        self._worker.start()

    def terminate(self):
        if not self._worker:
            return

        self._terminated = True
        self._worker.join()
        self._worker = None

    def _worker_loop(self):
        if not self.setup():
            return

        self._terminated = False
        while True:
            if not self.loop() or self._terminated:
                break
            time.sleep(0.1)

        self.teardown()

    def setup(self):
        pass

    def loop(self):
        raise NotImplementedError()

    def teardown(self):
        pass


class ApplicationError(Exception):
    pass
