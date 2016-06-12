# -*- coding: utf-8 -*-

import subprocess
import time

from pybot.raspi import i2c_bus
from pybot.youpi2.ctlpanel import Menu, Selector
from .__version__ import version
from .ctlpanel import ControlPanel

__author__ = 'Eric Pascual'


class TopLevel(object):
    TERMINATE = -9

    def __init__(self):
        self.pnl = ControlPanel(i2c_bus)

    def display_about(self):
        self.pnl.display_splash("""
        Youpi Control

        version %(version)s
        """ % {
            'version': version.split('+')[0]
        }, delay=2)

    def run(self):
        self.pnl.reset()
        self.display_about()

        menu = Menu(
            title='Main menu',
            choices={
                ControlPanel.Keys.BL: ('System', self.system_functions),
                ControlPanel.Keys.BR: ('Mode', self.mode_selector),
            },
            panel=self.pnl
        )

        while True:
            menu.display()
            if menu.handle_choice() == self.TERMINATE:
                break

        self.pnl.set_backlight(False)
        self.pnl.clear()
        self.pnl.leds_off()

    def mode_selector(self):
        sel = Selector(
            title='Select mode',
            choices=(
                ('Demo', self.demo_auto),
                ('Manual', self.manual_control),
                ('Network', self.web_service),
            ),
            panel=self.pnl
        )
        sel.display()
        return sel.handle_choice()

    def demo_auto(self):
        self.pnl.display_splash("""
        Automatic demo

        Hit a key to end
        """, delay=0)

        sequence = (self.pnl.Keys.TL, self.pnl.Keys.TR, self.pnl.Keys.BR, self.pnl.Keys.BL)
        progress = 0

        clock = 0
        self.pnl.set_leds(sequence[progress])

        while True:
            keys = self.pnl.get_keys()
            if keys:
                break
            time.sleep(0.1)

            now = time.time()
            if now - clock >= .2:
                progress = (progress + 1) % len(sequence)
                self.pnl.set_leds(sequence[progress])
                clock = now

        self.pnl.leds_off()

    def web_service(self):
        self.pnl.display_splash("""
        Web Services mode

        Stop combo to end
        """, delay=0)

        while True:
            keys = self.pnl.get_keys()
            if keys == {self.pnl.Keys.BL, self.pnl.Keys.BR}:
                break
            time.sleep(0.1)

    def manual_control(self):
        subprocess.call(['top'])

    def system_functions(self):
        sel = Selector(
            title='System',
            choices=(
                ('About', self.display_about_modal),
                ('Reset', self.reset_youpi),
                ('Shutdown', self.shutdown),
            ),
            panel=self.pnl
        )

        while True:
            sel.display()
            ret = sel.handle_choice()
            if ret in (Selector.ESC, self.TERMINATE):
                return ret

    def display_about_modal(self):
        self.display_about()

    def reset_youpi(self):
        self.pnl.clear()
        self.pnl.center_text_at("Resetting Youpi...", 2)

        time.sleep(2)

    def shutdown(self):
        sel = Selector(
            title='Shutdown',
            choices=(
                ('Quit', 'Q'),
                ('Reboot', 'R'),
                ('Power off', 'P'),
            ),
            panel=self.pnl
        )

        sel.display()
        action = sel.handle_choice()
        if action == Selector.ESC:
            return action

        elif action == 'R':
            self.pnl.display_progress("Reboot")
            subprocess.call('sudo reboot', shell=True)
        elif action == 'P':
            self.pnl.display_progress("Shutdown")
            subprocess.call('sudo poweroff', shell=True)

        return self.TERMINATE


def main():
    TopLevel().run()
