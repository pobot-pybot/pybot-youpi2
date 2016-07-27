# -*- coding: utf-8 -*-

""" Youpi top level controller

Manages the arm and the user interactions.
"""

import subprocess

from pybot.youpi2.__version__ import version

from pybot.youpi2.ctlpanel.widgets import Menu, Selector
from pybot.youpi2.ctlpanel.intf import ControlPanel
from pybot.youpi2.ctlpanel.devices.fs import ControlPanelDevice
from pybot.youpi2.ctlpanel.keys import Keys

from pybot.youpi2.shell.actions.about import DisplayAbout
from pybot.youpi2.shell.actions.extproc import DemoAuto, WebServicesControl, BrowserlUi, ManualControl, MinitelUi
from pybot.youpi2.shell.actions.youpi_system_actions import Reset, Disable

__author__ = 'Eric Pascual'


class Controller(object):
    SHUTDOWN = -9
    QUIT = -10

    def __init__(self):
        self.panel = ControlPanel(ControlPanelDevice('/mnt/lcdfs'))
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
                Keys.PREVIOUS: ('System', self.system_functions),
                Keys.NEXT: ('Mode', self.mode_selector),
            },
            panel=self.panel
        )

        while True:
            menu.display()
            action = menu.handle_choice()
            if action == self.QUIT:
                self.panel.leds_off()
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
    Controller().run()
