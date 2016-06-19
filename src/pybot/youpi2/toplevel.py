# -*- coding: utf-8 -*-

""" Youpi top level controller

Manages the arm and the user interactions.
"""

import subprocess
import time

from pybot.raspi import i2c_bus
from pybot.youpi2.ctlpanel import Menu, Selector
from .__version__ import version
from .ctlpanel import ControlPanel

from actions.about import DisplayAbout
from actions.demo_auto import StandAloneDemo
from actions.ws_control import WebServicesController
from actions.browser_ui import WebBrowserUi
from actions.minitel_ui import MinitelUi

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
                ControlPanel.Keys.BL: ('System', self.system_functions),
                ControlPanel.Keys.BR: ('Mode', self.mode_selector),
            },
            panel=self.panel
        )

        while True:
            menu.display()
            action = menu.handle_choice()
            if action in (self.SHUTDOWN, self.QUIT):
                self.panel.leds_off()
                if action == self.SHUTDOWN:
                    self.panel.set_backlight(False)
                    self.panel.clear()
                return

    def mode_selector(self):
        sel = Selector(
            title='Select mode',
            choices=(
                ('Demo', self.demo_auto),
                ('Manual', self.manual_control),
                ('Network', self.network_control),
            ),
            panel=self.panel
        )

        while True:
            sel.display()
            action = sel.handle_choice()
            if action == Selector.ESC:
                return

    def demo_auto(self):
        StandAloneDemo(self.panel, self.arm).execute()

    def network_control(self):
        sel = Selector(
            title='Network mode',
            choices=(
                ('Web services', WebServicesController(self.panel, self.arm).execute),
                ('Browser UI', WebBrowserUi(self.panel, self.arm).execute),
                ('Minitel UI', MinitelUi(self.panel, self.arm).execute),
            ),
            panel=self.panel
        )

        while True:
            sel.display()
            action = sel.handle_choice()
            if action == Selector.ESC:
                return

    # def web_services(self):
    #     WebServicesController(self.panel, self.arm).execute()
    #
    # def browser_ui(self):
    #     WebBrowserUi(self.panel, self.arm).execute()
    #
    # def minitel_ui(self):
    #     MinitelUi(self.panel, self.arm).execute()

    def manual_control(self):
        subprocess.call(['top'])

    def system_functions(self):
        sel = Selector(
            title='System',
            choices=(
                ('About', self.display_about_modal),
                ('Reset Youpi', self.reset_youpi),
                ('Disable Youpi', self.disable_youpi),
                ('Shutdown', self.shutdown),
            ),
            panel=self.panel
        )

        while True:
            sel.display()
            action = sel.handle_choice()
            if action in (Selector.ESC, self.SHUTDOWN, self.QUIT):
                return action

    def display_about_modal(self):
        self.display_about()

    def reset_youpi(self):
        self.panel.clear()
        self.panel.display_splash(
            """Place Youpi in
            home position, then
            press a button.
        """)
        self.panel.wait_for_key()
        self.panel.leds_off()
        self.panel.display_splash("Resetting Youpi...")

    def disable_youpi(self):
        # TODO disable Youpi motors
        self.panel.clear()
        self.panel.display_splash("""
            Youpi motors
            disabled
        """)

    def shutdown(self):
        sel = Selector(
            title='Shutdown',
            choices=(
                ('Quit application', 'Q'),
                ('Reboot', 'R'),
                ('Power off', 'P'),
            ),
            panel=self.panel
        )

        sel.display()
        action = sel.handle_choice()
        if action == Selector.ESC:
            return action

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
