# -*- coding: utf-8 -*-

from . import Action

__author__ = 'Eric Pascual'


class ManualControl(Action):
    def execute(self):
        self.panel.display_splash("""
        Manual control mode
        (not yet available)
        """, delay=0)

        self.panel.clear_was_locked_status()

        while True:
            self.panel.any_key_to_exit_message()

            if self.panel.get_keys():
                return

            time.sleep(0.1)


