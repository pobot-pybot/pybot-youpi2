# -*- coding: utf-8 -*-

import time

from pybot.lcd.lcd_i2c import LCD03
from pybot.raspi import i2c_bus

__author__ = 'Eric Pascual'


class ControlPanel(object):
    MENU_POSITIONS = {
        '1': (2, 1),
        '7': (4, 1),
        '3': (2, 20),
        '9': (4, 20),
    }

    def __init__(self):
        self.lcd = LCD03(i2c_bus)
        self.terminated = False

    def run(self):
        self.lcd.clear()
        self.lcd.set_backlight(True)

        self.terminated = False
        while not self.terminated:
            self.lcd.center_text_at("Main menu", 1)

            menu = {
                '1': ('Demo', self.demo_auto),
                '3': ('WS ctrl', self.web_service),
                '7': ('Reset', self.reset_youpi),
                '9': ('Shutdown', self.shutdown),
            }
            for key, entry in menu.iteritems():
                line, col = self.MENU_POSITIONS[key]
                label = entry[0]
                if col == 1:
                    self.lcd.write_at(line, col, '> ' + label)
                else:
                    s = label + ' <'
                    self.lcd.write_at(line, col - len(s) + 1, s)

            last_keys = []
            while True:
                keys = self.lcd.get_keys()
                if keys != last_keys:
                    try:
                        func = menu[keys[0]][1]
                    except KeyError:
                        pass
                    else:
                        func()

                    last_keys = keys
                time.sleep(0.2)

        self.lcd.set_backlight(False)
        self.lcd.clear()

    def demo_auto(self):
        pass

    def web_service(self):
        pass

    def reset_youpi(self):
        pass

    def shutdown(self):
        self.terminated = True


def main():
    pnl = ControlPanel()
    pnl.run()
