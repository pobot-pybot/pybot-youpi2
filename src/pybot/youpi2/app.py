# -*- coding: utf-8 -*-

import sys
import signal
import logging.config
import datetime

from pybot.core import cli
from pybot.core import log

from nros.core.commons import get_bus, get_node_proxy, get_node_interface
from nros.youpi2 import SERVICE_OBJECT_PATH, ARM_CONTROL_INTERFACE_NAME

from pybot.youpi2.ctlpanel import ControlPanel
from pybot.youpi2.ctlpanel.devices.fs import FileSystemDevice

__author__ = 'Eric Pascual'


class YoupiApplication(log.LogMixin):
    NAME = 'app'
    TITLE = "Youpi application"
    VERSION = None

    def __init__(self):
        # log_cfg = log.get_logging_configuration({
        #     'handlers': {
        #         'file': {
        #             'filename': log.log_file_path('youpi2-%s.log' % self.NAME)
        #         }
        #     },
        #     'root': {
        #         'handlers': ['file']
        #     }
        # })
        # logging.config.dictConfig(log_cfg)
        # self.logger = log.getLogger(self.__class__.__name__)
        log.LogMixin.__init__(self, name='youpi2-' + self.NAME)

        self.pnl = None
        self.arm = None
        self.terminated = False

    def main(self):
        parser = cli.get_argument_parser()
        parser.add_argument('--pnldev', default="/mnt/lcdfs")
        parser.add_argument('--arm-node-name', default="nros.youpi2")

        self.add_custom_arguments(parser)
        sys.exit(self.run(parser.parse_args()))

    def terminate(self, *args):
        self.terminated = True

    def run(self, args):
        self.log_starting_banner(self.VERSION)

        self.log_info('creating control panel device (path=%s)', args.pnldev)
        self.pnl = ControlPanel(FileSystemDevice(args.pnldev))

        self.log_info('getting access to the arm nROS node (name=%s)', args.arm_node_name)
        arm_node = get_node_proxy(get_bus(), args.arm_node_name, object_path=SERVICE_OBJECT_PATH)
        self.arm = get_node_interface(arm_node, interface_name=ARM_CONTROL_INTERFACE_NAME)

        signal.signal(signal.SIGTERM, self.terminate)

        self.pnl.clear()
        self.pnl.center_text_at(self.TITLE, line=1)

        try:
            self.log_info('invoking application setup')
            self.setup(**args.__dict__)
        except Exception as e:
            self.log_exception(e)
            self.on_run_error(e)
            return 1

        exit_code = 0
        try:
            self.log_info('starting application loop')
            loop_stop = False
            while not self.terminated and not loop_stop:
                loop_stop = self.loop()
        except Exception as e:
            self.log_exception(e)
            self.on_unexpected_error(e)
            exit_code = 1
        finally:
            self.log_info('invoking application teardown with exit_code=%s', exit_code)
            self.teardown(exit_code)

        self.log_info('returning with exit_code=%s', exit_code)
        return exit_code

    def add_custom_arguments(self, parser):
        pass

    def setup(self, **kwargs):
        pass

    def loop(self):
        pass

    def teardown(self, exit_code):
        pass

    def on_run_error(self, e):
        pass

    def on_unexpected_error(self, e):
        pass


class ApplicationError(Exception):
    pass
