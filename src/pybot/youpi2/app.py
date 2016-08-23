# -*- coding: utf-8 -*-

import sys
import signal
import os
import logging.config

from pybot.core import cli
from pybot.core import log

from pybot.youpi2.ctlpanel import ControlPanel
from pybot.youpi2.ctlpanel.devices.fs import FileSystemDevice

__author__ = 'Eric Pascual'


class YoupiApplication(object):
    NAME = 'app'
    TITLE = "Youpi application"

    def __init__(self):
        log_cfg = log.get_logging_configuration({
            'handlers': {
                'file': {
                    'filename': os.path.expanduser('~/youpi2-%s.log' % self.NAME)
                }
            },
            'root': {
                'handlers': ['file']
            }
        })
        logging.config.dictConfig(log_cfg)
        self.logger = log.getLogger(self.__class__.__name__)

        self.pnl = None
        self.terminated = False

    def main(self):
        parser = cli.get_argument_parser()
        parser.add_argument('--pnldev', default="/mnt/lcdfs")
        parser.add_argument('--armdev', default="/mnt/y2fs")

        self.add_custom_arguments(parser)
        sys.exit(self.run(parser.parse_args()))

    def terminate(self, *args):
        self.terminated = True

    def run(self, args):
        self.logger.info('creating control panel device (path=%s)', args.pnldev)
        self.pnl = ControlPanel(FileSystemDevice(args.pnldev))

        signal.signal(signal.SIGTERM, self.terminate)

        self.pnl.clear()
        self.pnl.center_text_at(self.TITLE, line=1)

        try:
            self.logger.info('invoking setup')
            self.setup()
        except Exception as e:
            self.logger.error(e)
            self.run_error(e)
            return 1

        exit_code = 0
        try:
            self.logger.info('starting loop')
            while not self.terminated:
                self.loop()
        except Exception as e:
            self.logger.error(e)
            self.unexpected_error(e)
            exit_code = 1
        finally:
            self.logger.info('invoking teardown with exit_code=%s', exit_code)
            self.teardown(exit_code)

        self.logger.info('returning with exit_code=%s', exit_code)
        return exit_code

    def add_custom_arguments(self, parser):
        pass

    def setup(self):
        pass

    def loop(self):
        pass

    def teardown(self, exit_code):
        pass

    def run_error(self, e):
        pass

    def unexpected_error(self, e):
        pass


class ApplicationError(Exception):
    pass
