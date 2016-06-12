# -*- coding: utf-8 -*-

import time

from pybot.lcd.lcd_i2c import LCD05

__author__ = 'Eric Pascual'


class ControlPanel(LCD05):
    EXPANDER_ADDR = 0x20
    KEYPAD_SCAN_PERIOD = 0.1
    KEYPAD_3x4_KEYS = '1245'

    class Keys(object):
        TL, TR, BL, BR = range(1, 5)
        ALL = (TL, TR, BL, BR)
        FIRST = ALL[0]

        @classmethod
        def mask(cls, keys=None):
            if keys:
                try:
                    iter(keys)
                except TypeError:
                    keys = [keys]
                return ~reduce(lambda x, y: x | y, [1 << (k - 1) for k in keys]) & 0xff
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
        self.keypad_fast_scan()

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
                k = keys.pop()
                if valid is None or k in valid:
                    return k
            time.sleep(self.KEYPAD_SCAN_PERIOD)

    def get_keys(self):
        keys = super(ControlPanel, self).get_keys()
        if keys:
            return {self.KEYPAD_3x4_KEYS.index(k) + self.Keys.FIRST for k in keys if k in self.KEYPAD_3x4_KEYS}
        else:
            return set()


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
        self.panel.leds_off()
        self.panel.center_text_at(self.title, 2)
        self.panel.center_text_at('-' * len(self.title), 3)

        for key, entry in self.choices.iteritems():
            line, col = self.MENU_POSITIONS[key]
            label = entry[0]
            if col == 1:
                self.panel.write_at(label, line, col)
            else:
                s = label
                self.panel.write_at(s, line, col - len(s) + 1)
        self.panel.set_leds(self.choices.keys())

    def handle_choice(self):
        key = self.panel.wait_for_key(valid=self.choices.keys())
        self.panel.leds_off()
        action = self.choices[key][1]
        return action() if callable(action) else action


class Selector(object):
    KEY_ESC = ControlPanel.Keys.TL
    KEY_OK = ControlPanel.Keys.TR
    KEY_PREV = ControlPanel.Keys.BL
    KEY_NEXT = ControlPanel.Keys.BR

    ESC = -1

    def __init__(self, title, choices, panel):
        self.title = title
        self.choices = choices
        self.choices_count = len(choices)
        self.panel = panel
        self.choice = 0
        self._w_choice = self.panel.width - 4

    def display(self):
        self.panel.clear()
        self.panel.leds_off()
        self.panel.center_text_at(self.title, line=2)
        l = "Esc"
        l += "OK".rjust(self.panel.width - len(l), " ")
        self.panel.write_at(l, line=1)
        self.panel.write_at('<' + ' ' * (self.panel.width - 2) + '>', line=4)
        self.panel.set_leds(ControlPanel.Keys.ALL)

    def handle_choice(self):
        while True:
            choice_descr = self.choices[self.choice]
            s = choice_descr[0][:self._w_choice]
            self.panel.write_at(s.center(self._w_choice), line=4, col=3)

            key = self.panel.wait_for_key()
            if key == self.KEY_ESC:
                return self.ESC

            elif key == self.KEY_OK:
                action = choice_descr[1]
                return action() if callable(action) else action

            elif key == self.KEY_PREV:
                self.choice = (self.choice - 1) % self.choices_count
            elif key == self.KEY_NEXT:
                self.choice = (self.choice + 1) % self.choices_count

            # wait for key is released
            while self.panel.get_keys():
                pass
