# -*- coding: utf-8 -*-

import subprocess
import time

from pybot.raspi import i2c_bus
from pybot.youpi2.ctlpanel import Menu, Selector
from .__version__ import version
from .ctlpanel import ControlPanel

__author__ = 'Eric Pascual'


class TopLevel(object):
    SHUTDOWN = -9
    QUIT = -10

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
            action = menu.handle_choice()
            if action in (self.SHUTDOWN, self.QUIT):
                break

        self.pnl.leds_off()
        if action == self.SHUTDOWN:
            self.pnl.set_backlight(False)
            self.pnl.clear()

    def mode_selector(self):
        sel = Selector(
            title='Select mode',
            choices=(
                ('Demo', self.demo_auto),
                ('Manual', self.manual_control),
                ('Network', self.network_control),
            ),
            panel=self.pnl
        )

        while True:
            sel.display()
            action = sel.handle_choice()
            if action == Selector.ESC:
                return

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

    def network_control(self):
        sel = Selector(
            title='Network mode',
            choices=(
                ('Web services', self.web_services),
                ('Browser UI', self.browser_ui),
                ('Minitel UI', self.minitel_ui),
            ),
            panel=self.pnl
        )

        while True:
            sel.display()
            action = sel.handle_choice()
            if action == Selector.ESC:
                return

    def web_services(self):
        self.pnl.leds_off()
        self.pnl.display_splash("""
        Web Services mode

        Stop combo to end
        """, delay=0)

        while True:
            keys = self.pnl.get_keys()
            if keys == {self.pnl.Keys.BL, self.pnl.Keys.BR}:
                break
            time.sleep(0.1)

    def browser_ui(self):
        self.pnl.leds_off()
        self.pnl.display_splash("""
        Browser UI mode

        Stop combo to end
        """, delay=0)

        while True:
            keys = self.pnl.get_keys()
            if keys == {self.pnl.Keys.BL, self.pnl.Keys.BR}:
                break
            time.sleep(0.1)

    def minitel_ui(self):
        self.pnl.leds_off()
        self.pnl.display_splash("""
        Minitel UI mode

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
            action = sel.handle_choice()
            if action in (Selector.ESC, self.SHUTDOWN, self.QUIT):
                return action

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

        elif action == 'Q':
            self.pnl.clear()
            self.pnl.write_at("I'll be back...")
            return self.QUIT

        elif action == 'R':
            self.pnl.display_progress("Reboot")
            subprocess.call('sudo reboot', shell=True)
        elif action == 'P':
            self.pnl.display_progress("Shutdown")
            subprocess.call('sudo poweroff', shell=True)

        return self.SHUTDOWN


def main():
    TopLevel().run()
