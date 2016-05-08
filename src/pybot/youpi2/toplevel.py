# -*- coding: utf-8 -*-

import time
import subprocess

from pybot.lcd.lcd_i2c import LCD03
from pybot.raspi import i2c_bus

from .__version__ import version

__author__ = 'Eric Pascual'


class MenuPanel(object):
    MENU_POSITIONS = {
        '1': (2, 1),
        '7': (4, 1),
        '3': (2, 20),
        '9': (4, 20),
    }

    def __init__(self, title, choices, lcd):
        self.title = title
        self.choices = choices
        self.lcd = lcd

    def display(self):
        self.lcd.clear()
        self.lcd.center_text_at(' ' + self.title + ' ', 1, '=')

        for key, entry in self.choices.iteritems():
            line, col = self.MENU_POSITIONS[key]
            label = entry[0]
            if col == 1:
                self.lcd.write_at('>' + label, line, col)
            else:
                s = label + '<'
                self.lcd.write_at(s, line, col - len(s) + 1)

    def get_and_process_input(self):
        last_keys = []
        func = None

        while True:
            keys = self.lcd.get_keys()
            if keys != last_keys:
                if keys:
                    try:
                        key = keys[0]
                        func = self.choices[key][1]
                    except KeyError:
                        pass

                    last_keys = keys

                else:
                    if func:
                        func()
                        break

            time.sleep(0.2)


class ControlPanel(object):
    def __init__(self):
        self.lcd = LCD03(i2c_bus)
        self.terminated = False
        self.shutdown_started = False

    def init_lcd_display(self):
        self.lcd.clear()
        self.lcd.set_backlight(True)
        self.lcd.set_cursor_type(LCD03.CT_INVISIBLE)

    def display_about(self, delay=2):
        self.lcd.clear()
        self.lcd.center_text_at("Youpi Control", 1)
        self.lcd.center_text_at("version " + version.split('+')[0], 3)

        time.sleep(delay)

    def _wait_for_any_key(self):
        while True:
            keys = self.lcd.get_keys()
            if keys:
                break
            time.sleep(0.2)

    def run(self):
        self.init_lcd_display()
        self.display_about()

        panel = MenuPanel(
            title='Main menu',
            choices={
                '1': ('Demo', self.demo_auto),
                '3': ('WS mode', self.web_service),
                '7': ('Man. ctrl', self.manual_control),
                '9': ('Tools', self.tools),
            },
            lcd=self.lcd
        )

        self.terminated = False
        while not self.terminated:
            panel.display()
            panel.get_and_process_input()

        self.lcd.set_backlight(False)
        self.lcd.clear()

    def demo_auto(self):
        self.lcd.clear()
        self.lcd.center_text_at(" Automatic demo ", 1, '=')
        self.lcd.center_text_at("Hit a key to end", 4)

        while True:
            keys = self.lcd.get_keys()
            if keys:
                break
            time.sleep(0.2)

    def web_service(self):
        pass

    def manual_control(self):
        subprocess.call(['top'])

    def exit_from_level(self):
        self.terminated = True

    def tools(self):
        panel = MenuPanel(
            title='Tools',
            choices={
                '1': ('Reset', self.reset_youpi),
                '3': ('Shutdown', self.shutdown),
                '7': ('About', self.display_about_modal),
                '9': ('Back', self.exit_from_level)
            },
            lcd=self.lcd
        )

        while not self.terminated:
            panel.display()
            panel.get_and_process_input()

        self.terminated = self.shutdown_started

    def display_about_modal(self):
        self.display_about(delay=0)
        self._wait_for_any_key()

    def reset_youpi(self):
        self.lcd.clear()
        self.lcd.center_text_at("Resetting Youpi...", 2)

        time.sleep(2)

    def shutdown(self):
        panel = MenuPanel(
            title='Shutdown',
            choices={
                '1': ('Quit', self.quit),
                '3': ('Reboot', self.reboot),
                '7': ('Power off', self.power_off),
                '9': ('Back', self.exit_from_level)
            },
            lcd=self.lcd
        )

        while not self.terminated:
            panel.display()
            panel.get_and_process_input()

        self.terminated = self.shutdown_started

    def quit(self):
        self.terminated = self.shutdown_started = True

    def reboot(self):
        self.lcd.clear()
        self.lcd.center_text_at("Reboot in progress...", 2)
        subprocess.call('sudo reboot', shell=True)

    def power_off(self):
        self.lcd.clear()
        self.lcd.center_text_at("Shutdown in progress...", 2)
        subprocess.call('sudo poweroff', shell=True)


def main():
    pnl = ControlPanel()
    pnl.run()
