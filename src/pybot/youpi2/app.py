# -*- coding: utf-8 -*-

import sys
import signal

from pybot.core import cli

from pybot.youpi2.ctlpanel import ControlPanel
from pybot.youpi2.ctlpanel.devices.fs import FileSystemDevice

__author__ = 'Eric Pascual'


class YoupiApplication(object):
    TITLE = "Youpi application"

    @staticmethod
    def main():
        app = YoupiApplication()

        parser = cli.get_argument_parser()
        parser.add_argument('--pnldev', default="/mnt/lcdfs")
        parser.add_argument('--armdev', default="/mnt/y2fs")

        app.add_custom_arguments(parser)
        sys.exit(app.run(parser.parse_args()))

    def __init__(self):
        self.pnl = None
        self.terminated = False

    def terminate(self, *args):
        self.terminated = True

    def run(self, args):
        self.pnl = ControlPanel(FileSystemDevice(args.pnldev))

        signal.signal(signal.SIGTERM, self.terminate)

        self.pnl.clear()
        self.pnl.center_text_at(self.TITLE, line=1)

        try:
            self.setup()
        except Exception as e:
            self.run_error(e)
            return 1

        exit_code = 0
        try:
            while not self.terminated:
                self.loop()
        except Exception as e:
            self.unexpected_error(e)
            exit_code = 1
        finally:
            self.teardown(exit_code)

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
