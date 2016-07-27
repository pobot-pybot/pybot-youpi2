# -*- coding: utf-8 -*-

import time
import subprocess

from pybot.lcd.lcd_i2c import LCD03

from pybot.youpi2.ctlpanel import Keys
from . import Action

__author__ = 'Eric Pascual'


class ExternalProcessAction(Action):
    COMMAND = None
    TITLE = None

    def execute(self):
        self.panel.center_text_at(self.TITLE, line=2)

        # start the demonstration as a child process
        try:
            app_proc = subprocess.Popen(self.COMMAND, shell=True)

        except OSError as e:
            self.panel.clear()
            self.panel.center_text_at("ERROR", line=2)
            self.panel.center_text_at(e.message[:20], line=3)
            self.panel.center_text_at(e.message[20:40], line=4)
            self.panel.write_at(LCD03.CH_OK, 1, self.panel.width)
            self.panel.wait_for_key([Keys.OK])

        else:
            self.panel.clear_was_locked_status()

            exit_keys = [Keys.ESC]
            while True:
                self.panel.exit_key_message()

                if self.panel.get_keys() == exit_keys:
                    app_proc.terminate()
                    app_proc.wait(30)
                    return

                time.sleep(0.1)


class MinitelUi(ExternalProcessAction):
    COMMAND = "youpi2-minitel"
    TITLE = "Minitel control mode"


class ManualControl(ExternalProcessAction):
    COMMAND = "youpi2-manual"
    TITLE = "Manual control mode"


class WebServicesControl(ExternalProcessAction):
    COMMAND = "youpi2-ws"
    TITLE = "Web Services mode"


class BrowserlUi(ExternalProcessAction):
    COMMAND = "youpi2-browser"
    TITLE = "Web Services mode"


class DemoAuto(ExternalProcessAction):
    COMMAND = "youpi2-demo-auto"
    TITLE = "Automatic demo mode"
