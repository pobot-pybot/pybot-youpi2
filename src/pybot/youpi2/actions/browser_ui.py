# -*- coding: utf-8 -*-

import time

from . import Action

__author__ = 'Eric Pascual'


class WebBrowserUi(Action):
    def execute(self):
        self.panel.leds_off()
        self.panel.display_splash("""
        Browser UI mode

        Stop combo to end
        """, delay=0)

        while True:
            keys = self.panel.get_keys()
            if keys == {self.panel.Keys.BL, self.panel.Keys.BR}:
                break
            time.sleep(0.1)

