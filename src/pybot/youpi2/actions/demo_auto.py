# -*- coding: utf-8 -*-

import time

from . import Action

__author__ = 'Eric Pascual'


class StandAloneDemo(Action):
    def prepare(self):
        # TODO self.arm.disable()

        self.panel.display_splash(
            """Place arm in neutral
            position and hit
            any key.
            """, delay=0)

    def execute(self):
        self.prepare()

        self.panel.display_splash("""
        Automatic demo mode
        """, delay=-1)

        self.panel.clear_was_locked_status()

        sequence = (self.panel.Keys.TL, self.panel.Keys.TR, self.panel.Keys.BR, self.panel.Keys.BL)
        progress = 0

        clock = 0

        self.panel.set_leds(sequence[progress])
        while True:
            self.panel.any_key_to_exit_message()

            if self.panel.get_keys():
                return

            time.sleep(0.1)

            now = time.time()
            if now - clock >= .2:
                progress = (progress + 1) % len(sequence)
                self.panel.set_leds(sequence[progress])
                clock = now
