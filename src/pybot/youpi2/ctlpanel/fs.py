# -*- coding: utf-8 -*-

import os
import string
import time

from .keys import Keys

__author__ = 'Eric Pascual'


class ControlPanel(object):
    F_BACKLIGHT = 'backlight'
    F_BRIGHTNESS = 'brightness'
    F_KEYS = 'keys'
    F_DISPLAY = 'display'
    F_INFO = 'info'
    F_CONTRAST = 'contrast'
    F_LEDS = 'leds'
    F_LOCKED = 'locked'

    _READ_WRITE = {
        F_BACKLIGHT: True,
        F_KEYS: True,
        F_DISPLAY: True,
        F_INFO: False,
        F_CONTRAST: True,
        F_BRIGHTNESS: True,
        F_LEDS: True,
        F_LOCKED: False,
    }

    KEYPAD_SCAN_PERIOD = 0.1
    KEYPAD_3x4_KEYS = '1245'
    WAIT_FOR_EVER = -1

    def __init__(self, mount_point, debug=False):
        if not os.path.isdir(mount_point):
            raise ValueError('mount point not found : %s' % mount_point)

        self._debug = debug

        self.was_locked = False

        self._mount_point = mount_point
        self._fs_files = {
            n: open(os.path.join(mount_point, n), 'w' if self._READ_WRITE[n] else 'r', 0)
            for n in os.listdir(mount_point)
        }

        self._info = {}
        for line in self._fs_files[self.F_INFO].readlines():
            attr, value = (j.strip() for j in line.split(':'))
            try:
                value = int(value)
            except ValueError:
                pass
            self._info[attr] = value
        self._width = self._info['cols']
        self._height = self._info['rows']

    def _fp(self, name):
        try:
            return self._fs_files[name]
        except KeyError:
            raise TypeError("not supported")

    @property
    def leds(self):
        return int(self._fp(self.F_LEDS).read())

    @leds.setter
    def leds(self, state):
        self._fp(self.F_LEDS).write(str(state))

    def set_leds(self, keys=None):
        """ Turns a set of LEDs on.

        .. seealso:: :py:meth:`Keys.mask` for parameter definition.
        """
        self.leds = Keys.mask(keys)

    def leds_off(self):
        """ Convenience function for turning all the LEDs off. """
        self.leds = 0

    def is_locked(self):
        """ Tells if the lock switch is on or off.
        """
        return bool(int(self._fp(self.F_LOCKED).read()))

    @property
    def backlight(self):
        return bool(int(self._fp(self.F_BACKLIGHT).read()))

    @backlight.setter
    def backlight(self, on):
        self._fp(self.F_BACKLIGHT).write('1' if on else '0')

    def reset(self):
        """ Resets the panel by chaining the following operations :

        * clear the display
        * turns the back light on
        * turns the cursor display off
        * turns all the keypad LEDs off
        * set the keypad scanner of the LCD controller in fast mode
        """
        self.clear()
        self.backlight = True
        self.leds_off()

    def clear(self):
        self._fp(self.F_DISPLAY).write('\x0c')

    def display_splash(self, text, delay=2):
        """ Displays a page of text and waits before returning.

        If a wait is provided (as a number of seconds) the method waits
        before returning. If `WAIT_FOR_EVER` (or any negative delay) is passed,
        an infinite wait is done, ended by pressing one of the keypad keys.

        :param str text: the lines of text, separated by newlines ('\n')
        :param int delay: the number of seconds to wait before returning.
        If < 0, a key wait is used instead of a time delay.
        """
        self.clear()
        for i, line in enumerate(text.split('\n', 3)):
            self.center_text_at(line.strip(), i + 1)

        if delay >= 0:
            if delay:
                time.sleep(delay)
        else:
            self.wait_for_key()

    def center_text_at(self, s, line, fill_char=' '):
        """ Convenience method to write a centered text on a given line.

        Arguments:
            s:
                the text
            line:
                the text line
            fill_char:
                padding character
        """
        self.write_at(string.center(s, self._width, fill_char), line, 1)

    def write_at(self, s, line=1, col=1):
        """ Convenience method to write a text at a given location.

        Arguments:
            s:
                the text
            line, col:
                the text position
        """
        self.write("\x1b[%d;%dH%s" % (line, col, s))

    def write(self, s):
        self._fp(self.F_DISPLAY).write(s)

    def display_progress(self, msg):
        """ Displays a 'xxx in progress''' message, centered on the LCD.

        :param str msg: the task in progress
        """
        self.clear()
        self.leds_off()
        self.center_text_at(msg, 2)
        self.center_text_at("in progress...", 3)

    def wait_for_key(self, valid=None):
        """ Waits for a key to be pressed and return it.

        In case of multiple presses (chord), only the first one is returned.
        Sorting sequence is the one defined by the `Keys.ALL` predefined set.

        :param valid: an optional set or list of keys, if the expected one must
        belong to a specific subset
        :return: the pressed key
        :rtype: int
        """
        valid = valid or Keys.ALL
        while True:
            if self.is_locked():
                self.leds_off()
            else:
                self.set_leds(valid)

            keys = self.get_keys()
            if keys:
                k = keys.pop()
                if k in valid:
                    return k
            time.sleep(self.KEYPAD_SCAN_PERIOD)

    def get_keypad_state(self):
        return int(self._fp(self.F_KEYS).read())

    @staticmethod
    def state_to_keys(state):
        """ Converts a keypad state bit field into the corresponding
        set of keys. """
        keys = set()
        for k in '123456789*0#':
            if state & 1:
                keys.add(k)
            state >>= 1
        return keys

    def get_keys(self):
        """ Overridden version if the inherited :py:meth:`LCD05.get_keys` method, converting
        default key identifications to the ones used by the panel.

        The panel lock switch is tested first for input inhibition.

        .. seealso:: :py:meth:`LCD05.get_keys`
        """
        if self.is_locked():
            return set()

        keys = self.state_to_keys(self.get_keypad_state())
        if keys:
            return {self.KEYPAD_3x4_KEYS.index(k) + Keys.FIRST for k in keys if k in self.KEYPAD_3x4_KEYS}
        else:
            return set()

    def clear_was_locked_status(self):
        self.was_locked = None

    def any_key_to_exit_message(self, msg='Press a key to exit', line=4):
        """ Displays the invitation message if the panel is unlocked"""
        is_locked = self.is_locked()
        if self.was_locked is None or is_locked != self.was_locked:
            if is_locked:
                self.write_at(' ' * self._width, line=line)
                self.leds_off()
            else:
                self.center_text_at(msg, line=line)
                self.set_leds(Keys.ALL)

            self.was_locked = is_locked
