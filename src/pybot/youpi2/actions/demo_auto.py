# -*- coding: utf-8 -*-

import time

from . import Action

__author__ = 'Eric Pascual'


class StandAloneDemo(Action):
    def execute(self):
        self.panel.display_splash("""
        Automatic demo

        Hit a key to end
        """, delay=0)

        sequence = (self.panel.Keys.TL, self.panel.Keys.TR, self.panel.Keys.BR, self.panel.Keys.BL)
        progress = 0

        clock = 0
        self.panel.set_leds(sequence[progress])

        while True:
            keys = self.panel.get_keys()
            if keys:
                break
            time.sleep(0.1)

            now = time.time()
            if now - clock >= .2:
                progress = (progress + 1) % len(sequence)
                self.panel.set_leds(sequence[progress])
                clock = now

        self.panel.leds_off()

