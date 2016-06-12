# -*- coding: utf-8 -*-

import time
import subprocess
from inspect import isfunction

from pybot.raspi import i2c_bus

from .__version__ import version
from .ctlpanel import ControlPanel

__author__ = 'Eric Pascual'


class Menu(object):
    MENU_POSITIONS = {
        ControlPanel.Keys.TL: (1, 1),
        ControlPanel.Keys.BL: (4, 1),
        ControlPanel.Keys.TR: (1, 20),
        ControlPanel.Keys.BR: (4, 20),
    }

    BACK = -1

    def __init__(self, title, choices, panel):
        self.title = title
        self.choices = choices
        self.panel = panel

    def display(self):
        self.panel.clear()
        self.panel.set_leds()
        self.panel.center_text_at(self.title, 2)
        self.panel.center_text_at('-' * len(self.title), 3)

        for key, entry in self.choices.iteritems():
            line, col = self.MENU_POSITIONS[key]
            label = entry[0]
            if col == 1:
                self.panel.write_at('<' + label, line, col)
            else:
                s = label + '>'
                self.panel.write_at(s, line, col - len(s) + 1)
        self.panel.set_leds(self.choices.keys())

    def get_and_process_input(self):
        key = self.panel.wait_for_key(valid=self.choices.keys())
        self.panel.leds_off()
        action = self.choices[key][1]
        return action() if isfunction(action) else action


class TopLevel(object):
    TERMINATE = -1

    def __init__(self):
        self.pnl = ControlPanel(i2c_bus)
        self.terminated = False

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
                ControlPanel.Keys.TL: ('Demo', self.demo_auto),
                ControlPanel.Keys.TR: ('WS mode', self.web_service),
                ControlPanel.Keys.BL: ('Man. ctrl', self.manual_control),
                ControlPanel.Keys.BR: ('Tools', self.tools),
            },
            panel=self.pnl
        )

        terminated = False
        while not terminated:
            menu.display()
            terminated = menu.get_and_process_input() == self.TERMINATE

        self.pnl.set_backlight(False)
        self.pnl.clear()
        self.pnl.set_leds()

    def demo_auto(self):
        self.pnl.display_splash("""
        Automatic demo

        Hit a key to end
        """, delay=0)

        sequence = self.pnl.Keys.ALL
        progress = 0

        clock = 0
        self.pnl.set_leds(sequence[progress])

        while True:
            keys = self.pnl.get_keys()
            if keys:
                break
            time.sleep(0.1)

            now = time.time()
            if now - clock >= .5:
                progress = (progress + 1) % len(sequence)
                self.pnl.set_leds(sequence[progress])
                clock = now

        self.pnl.set_leds()

    def web_service(self):
        pass

    def manual_control(self):
        subprocess.call(['top'])

    def tools(self):
        menu = Menu(
            title='Tools',
            choices={
                ControlPanel.Keys.TL: ('Reset', self.reset_youpi),
                ControlPanel.Keys.TR: ('Shutdown', self.shutdown),
                ControlPanel.Keys.BL: ('About', self.display_about_modal),
                ControlPanel.Keys.BR: ('Back', Menu.BACK)
            },
            panel=self.pnl
        )

        done = False
        while not done:
            menu.display()
            done = menu.get_and_process_input() == Menu.BACK

    def display_about_modal(self):
        self.display_about()

    def reset_youpi(self):
        self.pnl.clear()
        self.pnl.center_text_at("Resetting Youpi...", 2)

        time.sleep(2)

    def shutdown(self):
        panel = Menu(
            title='Shutdown',
            choices={
                ControlPanel.Keys.TL: ('Quit', 'Q'),
                ControlPanel.Keys.TR: ('Reboot', 'R'),
                ControlPanel.Keys.BL: ('Power off', 'P'),
                ControlPanel.Keys.BR: ('Back', Menu.BACK)
            },
            panel=self.pnl
        )

        panel.display()
        action = panel.get_and_process_input()
        if action == Menu.BACK:
            return
        elif action == 'R':
            self.pnl.display_progress("Reboot")
            subprocess.call('sudo reboot', shell=True)
        elif action == 'P':
            self.pnl.display_progress("Shutdown")
            subprocess.call('sudo poweroff', shell=True)

        self.terminated = True


def main():
    TopLevel().run()
