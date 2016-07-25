# -*- coding: utf-8 -*-

from . import Action

__author__ = 'Eric Pascual'


class Reset(Action):
    def execute(self):
        self.panel.clear()
        self.panel.display_splash(
            """Place Youpi in
            home position, then
            press a button.
        """)
        self.panel.wait_for_key()
        self.panel.leds_off()
        self.panel.display_splash("Resetting Youpi...")


class Disable(Action):
    def execute(self):
        # TODO disable Youpi motors
        self.panel.clear()
        self.panel.display_splash("""
            Youpi motors
            are disabled
        """)
