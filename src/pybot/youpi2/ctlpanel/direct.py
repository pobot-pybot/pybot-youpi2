# -*- coding: utf-8 -*-

""" This module provides classes for managing Youpi's control panel.

The control panel is composed of a LCD05 4x20 LCD display, associated to
a reduced matrix keypad (2x2 keys). LEDs are integrated in the key buttons
and can be controlled by software.

Both the LCD and the LEDs use I2C to communicate, the LEDs being driven
by an I2C IO expander (PCF8574).
"""

import time

from pybot.lcd.lcd_i2c import LCD05
from .keys import Keys

__author__ = 'Eric Pascual'


class ControlPanel(LCD05):
    """ An extended version of the LCD05 driver class, adding methods for
    control the key LEDs.

    It provides also a modified view of the keypad, replacing the identification
    of the keys by the digits printed on their faces by their position (top-left,
    top-right,...).
    """

    EXPANDER_ADDR = 0x20
    KEYPAD_SCAN_PERIOD = 0.1
    KEYPAD_3x4_KEYS = '1245'
    WAIT_FOR_EVER = -1

    def __init__(self, bus, debug=False):
        super(LCD05, self).__init__(bus, debug=debug)
        self.was_locked = False

    @property
    def leds(self):
        port_state = self._bus.read_byte(self.EXPANDER_ADDR)
        return ~port_state & 0x0f

    @leds.setter
    def leds(self, state):
        # Remember we work in inverted logic at expander level, since connected
        # in sink mode => invert the LED states to obtain the port ones.
        port_state = ~state
        # Take care also to set other IOs as inputs (0xf0 mask)
        self._bus.write_byte(self.EXPANDER_ADDR, port_state | 0xf0)

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

        The lock switch must be connected to P7 PCF IO, and must pull the input
        down to the ground when closed. Since the security switch used here is opened
        when the key removal position, the HIGH state corresponds to "locked".
        """
        return bool(self._bus.read_byte(self.EXPANDER_ADDR) & 0x80)

    def reset(self):
        """ Resets the panel by chaining the following operations :

        * clear the display
        * turns the back light on
        * turns the cursor display off
        * turns all the keypad LEDs off
        * set the keypad scanner of the LCD controller in fast mode
        """
        super(ControlPanel, self).reset()
        self.leds_off()

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

    def get_keys(self):
        """ Overridden version if the inherited :py:meth:`LCD05.get_keys` method, converting
        default key identifications to the ones used by the panel.

        The panel lock switch is tested first for input inhibition.

        .. seealso:: :py:meth:`LCD05.get_keys`
        """
        if self.is_locked():
            return set()

        keys = super(ControlPanel, self).get_keys()
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
                self.write_at(' ' * self.width, line=line)
                self.leds_off()
            else:
                self.center_text_at(msg, line=line)
                self.set_leds(Keys.ALL)

            self.was_locked = is_locked


