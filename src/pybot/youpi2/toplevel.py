# -*- coding: utf-8 -*-

""" Youpi top level controller

Manages the arm and the user interactions.
"""

import subprocess

from pybot.raspi import i2c_bus
from pybot.youpi2.ctlpanel.widgets import Menu, Selector
from .__version__ import version
from .ctlpanel.fs import ControlPanel
from .ctlpanel.keys import Keys

from actions.about import DisplayAbout
from actions.demo_auto import StandAloneDemo
from actions.ws_control import WebServicesController
from actions.browser_ui import WebBrowserUi
from actions.minitel_ui import MinitelUi
from actions.manual_control import ManualControl
from actions.youpi_system_actions import Reset, Disable

__author__ = 'Eric Pascual'


class TopLevel(object):
    SHUTDOWN = -9
    QUIT = -10

    def __init__(self):
        self.panel = ControlPanel(i2c_bus)
        # TODO
        self.arm = None

    def display_about(self):
        DisplayAbout(self.panel, None, version=version).execute()

    def run(self):
        self.panel.reset()
        self.display_about()

        menu = Menu(
            title='Main menu',
            choices={
                Keys.BL: ('System', self.system_functions),
                Keys.BR: ('Mode', self.mode_selector),
            },
            panel=self.panel
        )

        while True:
            menu.display()
            action = menu.handle_choice()
            if action in (self.SHUTDOWN, self.QUIT):
                self.panel.leds_off()
                if action == self.SHUTDOWN:
                    self.panel.backlight = False
                    self.panel.clear()
                return

    def sublevel(self, title, choices, exit_on=None):
        sel = Selector(
            title=title,
            choices=choices,
            panel=self.panel
        )

        exit_on = exit_on or [Selector.ESC]
        while True:
            sel.display()
            action = sel.handle_choice()
            if action in exit_on:
                return action

    def mode_selector(self):
        action = self.sublevel(
            title='Select mode',
            choices=(
                ('Demo', StandAloneDemo(self.panel, self.arm).execute),
                ('Manual', ManualControl(self.panel, self.arm).execute),
                ('Network', self.network_control),
            )
        )
        if action != Selector.ESC:
            return action

    def network_control(self):
        action = self.sublevel(
            title='Network mode',
            choices=(
                ('Web services', WebServicesController(self.panel, self.arm).execute),
                ('Browser UI', WebBrowserUi(self.panel, self.arm).execute),
                ('Minitel UI', MinitelUi(self.panel, self.arm).execute),
            )
        )
        if action != Selector.ESC:
            return action

    def system_functions(self):
        return self.sublevel(
            title='System',
            choices=(
                ('About', self.display_about_modal),
                ('Reset Youpi', Reset(self.panel, self.arm).execute),
                ('Disable Youpi', Disable(self.panel, self.arm).execute),
                ('Shutdown', self.shutdown),
            ),
            exit_on=(Selector.ESC, self.SHUTDOWN, self.QUIT)
        )

    def display_about_modal(self):
        self.display_about()

    def shutdown(self):
        action = self.sublevel(
            title='Shutdown',
            choices=(
                ('Quit to shell', 'Q'),
                ('Reboot', 'R'),
                ('Power off', 'P'),
            ),
            exit_on=(Selector.ESC, 'Q', 'R', 'P')
        )

        if action == Selector.ESC:
            return

        elif action == 'Q':
            self.panel.clear()
            self.panel.write_at("I'll be back...")
            return self.QUIT

        elif action == 'R':
            self.panel.display_progress("Reboot")
            subprocess.call('sudo reboot', shell=True)
        elif action == 'P':
            self.panel.display_progress("Shutdown")
            subprocess.call('sudo poweroff', shell=True)

        return self.SHUTDOWN


def main():
    TopLevel().run()
