# -*- coding: utf-8 -*-

import time

from pybot.lcd.lcd_i2c import LCD05

__author__ = 'Eric Pascual'


class ControlPanel(LCD05):
    EXPANDER_ADDR = 0x20
    KEYPAD_SCAN_PERIOD = 0.1

    class Keys(object):
        TL, TR, BL, BR = range(1, 5)
        ALL = (TL, TR, BL, BR)
        FIRST = ALL[0]

        @classmethod
        def mask(cls, keys=None):
            if keys:
                return ~reduce(lambda x, y: x | y, [1 << k for k in keys]) & 0xff
            else:
                return 0x0f

    def __init__(self, bus, debug=False):
        super(LCD05, self).__init__(bus, debug=debug)

    def set_leds(self, keys=None):
        self._bus.write_byte_data(self.EXPANDER_ADDR, 0, self.Keys.mask(keys))

    def leds_off(self):
        self.set_leds()

    def reset(self):
        self.clear()
        self.set_backlight(True)
        self.set_cursor_type(ControlPanel.CT_INVISIBLE)
        self.leds_off()

    def display_splash(self, text, delay=2):
        self.clear()
        for i, line in enumerate(text.split('\n', 3)):
            self.center_text_at(line.strip(), i + 1)

        if delay >= 0:
            if delay:
                time.sleep(delay)
        else:
            self.wait_for_key()

    def display_progress(self, msg):
        self.leds_off()
        self.center_text_at(msg, 2)
        self.center_text_at("in progress...", 3)

    def wait_for_key(self, valid=None):
        while True:
            keys = self.get_keys()
            if keys:
                k = keys[0]
                if valid is None or k in valid:
                    return k
            time.sleep(self.KEYPAD_SCAN_PERIOD)

    def get_keys(self):
        return ['1245'.index(k) + self.Keys.FIRST for k in super(ControlPanel, self).get_keys()]
