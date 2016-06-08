# -*- coding: utf-8 -*-

import time
import subprocess

from pybot.raspi import i2c_bus

from .__version__ import version
from .panel import LCDPanel

__author__ = 'Eric Pascual'


class MenuPanel(object):
    MENU_POSITIONS = {
        '1': (1, 1),
        '4': (4, 1),
        '2': (1, 20),
        '5': (4, 20),
    }

    def __init__(self, title, choices, lcd):
        self.title = title
        self.choices = choices
        self.lcd = lcd

    def display(self):
        self.lcd.clear()
        self.lcd.center_text_at(self.title, 2)
        self.lcd.center_text_at('-' * len(self.title), 3)

        for key, entry in self.choices.iteritems():
            line, col = self.MENU_POSITIONS[key]
            label = entry[0]
            if col == 1:
                self.lcd.write_at('<' + label, line, col)
            else:
                s = label + '>'
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
        self.lcd = LCDPanel(i2c_bus)
        self.terminated = False
        self.shutdown_started = False

    def init_lcd_display(self):
        self.lcd.clear()
        self.lcd.set_backlight(True)
        self.lcd.set_cursor_type(LCDPanel.CT_INVISIBLE)

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
                LCDPanel.TL_KEY: ('Demo', self.demo_auto),
                LCDPanel.TR_KEY: ('WS mode', self.web_service),
                LCDPanel.BL_KEY: ('Man. ctrl', self.manual_control),
                LCDPanel.BR_KEY: ('Tools', self.tools),
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

        sequence = '1254'
        progress = 0

        clock = 0
        self.lcd.set_leds(sequence[progress])

        while True:
            keys = self.lcd.get_keys()
            if keys:
                break
            time.sleep(0.1)

            now = time.time()
            if now - clock >= 1:
                progress = (progress + 1) % len(sequence)
                self.lcd.set_leds([sequence[progress]])
                clock = now

        self.lcd.set_leds()

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
                LCDPanel.TL_KEY: ('Reset', self.reset_youpi),
                LCDPanel.TR_KEY: ('Shutdown', self.shutdown),
                LCDPanel.BL_KEY: ('About', self.display_about_modal),
                LCDPanel.BR_KEY: ('Back', self.exit_from_level)
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
                LCDPanel.TL_KEY: ('Quit', self.quit),
                LCDPanel.TR_KEY: ('Reboot', self.reboot),
                LCDPanel.BL_KEY: ('Power off', self.power_off),
                LCDPanel.BR_KEY: ('Back', self.exit_from_level)
            },
            lcd=self.lcd
        )

        while not self.terminated:
            panel.display()
            panel.get_and_process_input()

        self.terminated = self.shutdown_started

    def quit(self):
        self.terminated = self.shutdown_started = True

    def in_progress(self, msg):
        self.lcd.clear()
        self.lcd.center_text_at(msg, 2)
        self.lcd.center_text_at("in progress...", 3)

    def reboot(self):
        self.in_progress("Reboot")
        subprocess.call('sudo reboot', shell=True)

    def power_off(self):
        self.in_progress("Shutdown")
        subprocess.call('sudo poweroff', shell=True)


def main():
    pnl = ControlPanel()
    pnl.run()
