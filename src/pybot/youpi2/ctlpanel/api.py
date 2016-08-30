# -*- coding: utf-8 -*-

import time
import string

import evdev

from .keys import Keys

__author__ = 'Eric Pascual'


class ControlPanel(object):
    KEYPAD_SCAN_PERIOD = 0.1
    KEYPAD_3x4_KEYS = '1245'
    WAIT_FOR_EVER = -1
    EVDEV_DEVICE_NAME = 'ctrl-panel'

    EVKEY_TO_PNLKEY = {
        evdev.ecodes.KEY_ESC: Keys.ESC,
        evdev.ecodes.KEY_OK: Keys.OK,
        evdev.ecodes.KEY_PREVIOUS: Keys.PREVIOUS,
        evdev.ecodes.KEY_NEXT: Keys.NEXT,
    }

    def __init__(self, device, debug=False):
        """
        :param device: an instance of the real device
        :param bool debug: activates the debug mode
        """
        if not device:
            raise ValueError('device parameter is mandatory')

        self._check_device_type(device)
        self._device = device

        self._debug = debug
        self.was_locked = False

        self._active = True

        self._evdev = None
        for dev_path in evdev.list_devices():
            dev = evdev.InputDevice(dev_path)
            if dev.name == self.EVDEV_DEVICE_NAME:
                self._evdev = dev
                break

    def terminate(self):
        """ Clears the active internal flag so that a currently running wait loop will
        exit.

        This is intended to be used by application signal handlers for a clean shutdown
        when a SIGTERM or SIGINT (or any specific termination signal) is received.
        """
        self._active = False

    @staticmethod
    def _check_device_type(device):
        required_attrs = (
            'width', 'height',
            'get_leds_state', 'get_leds_state',
            'is_locked',
            'get_backlight', 'set_backlight',
            'clear',
            'write', 'write_at',
            'get_keypad_state',
            'reset'
        )
        for attr in required_attrs:
            if not hasattr(device, attr):
                raise TypeError('attribute missing from device : %s' % attr)

    @property
    def width(self):
        return self._device.width

    @property
    def height(self):
        return self._device.height

    @property
    def leds(self):
        return self._device.get_leds_state()

    @leds.setter
    def leds(self, state):
        self._device.set_leds_state(state)

    def set_leds(self, keys=None):
        """ Turns a set of LEDs on.

        .. seealso:: :py:meth:`Keys.mask` for parameter definition.
        """
        self.leds = ~Keys.mask(keys) & 0x0f

    def leds_off(self):
        """ Convenience function for turning all the LEDs off. """
        self.leds = 0

    def is_locked(self):
        """ Tells if the lock switch is on or off.
        """
        return self._device.is_locked()

    @property
    def backlight(self):
        return self._device.get_backlight()

    @backlight.setter
    def backlight(self, on):
        self._device.set_backlight(on)

    def reset(self):
        """ Resets the panel by chaining the following operations :

        * clear the display
        * turns the back light on
        * turns the cursor display off
        * turns all the keypad LEDs off
        * set the keypad scanner of the LCD controller in fast mode
        """
        self._device.reset()

    def clear(self):
        self._device.clear()

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

        :param str s: the text
        :param int line: the text line
        :param chr fill_char: padding character
        """
        self.write_at(string.center(s, self.width, fill_char), line, 1)

    def write_at(self, s, line=1, col=1):
        """ Convenience method to write a text at a given location.

        :param str s: the text
        :param int line: the text position (line)
        :param int col: the text position (column)
        """
        self._device.write_at(s, line, col)

    def write(self, s):
        self._device.write(s)

    def display_progress(self, msg):
        """ Displays a 'xxx in progress''' message, centered on the LCD.

        :param str msg: the task in progress
        """
        self.clear()
        self.leds_off()
        self.center_text_at(msg, 2)
        self.center_text_at("in progress...", 3)

    def countdown(self, msg, delay=3, can_abort=False):
        """ Displays a message with a countdown and exists when it reaches 0.

        Do nothing if delay is 0 or negative

        :param str msg: the message to be displayed
        :param int delay: the countdown delay (in seconds)
        :param bool can_abort: True if the countdown can be aborted by the ESC key
        :return: True if delay elapsed, False if interrupted by abort key usage or invalid delay
        :rtype: bool
        """
        if delay <= 0:
            return False

        self.clear()
        self.leds_off()
        self.center_text_at(msg, 1)

        abort_keys = {Keys.ESC}
        if can_abort:
            self.center_text_at("ESC : Cancel", 4)
            self.set_leds(Keys.ESC)

        refresh_time = now = time.time()
        end_time = now + delay
        try:
            while self._active:
                now = time.time()
                if now >= end_time:
                    self.center_text_at("NOW", 2)
                    return True

                if can_abort and self.get_keys() == abort_keys:
                    return False

                if now >= refresh_time:
                    self.center_text_at("in %d seconds..." % delay, 2)
                    refresh_time += 1
                    delay -= 1

                time.sleep(self.KEYPAD_SCAN_PERIOD)

        finally:
            self.leds_off()

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
        self.clear_was_locked_status()
        while self._active:
            # update LEDs state if relevant
            is_locked = self.is_locked()
            if self.was_locked is None or self.was_locked != is_locked:
                if is_locked:
                    self.leds_off()
                else:
                    self.set_leds(valid)
                self.was_locked = is_locked

            keys = self.get_keys()
            if keys:
                k = keys.pop()
                if k in valid:
                    return k

            time.sleep(self.KEYPAD_SCAN_PERIOD)

    def get_keypad_state(self):
        return self._device.get_keypad_state()

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

        if self._evdev:
            return {self.EVKEY_TO_PNLKEY[k] for k in self._evdev.active_keys()}

        else:
            keys = self.state_to_keys(self.get_keypad_state())
            if keys:
                return {self.KEYPAD_3x4_KEYS.index(k) + Keys.FIRST for k in keys if k in self.KEYPAD_3x4_KEYS}
            else:
                return set()

    def clear_was_locked_status(self):
        self.was_locked = None

    def any_key_to_exit_message(self, msg='Press a key to exit', line=4):
        """ Displays the invitation message if the panel is unlocked """
        is_locked = self.is_locked()
        if self.was_locked is None or is_locked != self.was_locked:
            if is_locked:
                self.write_at(' ' * self.width, line=line)
                self.leds_off()
            else:
                self.center_text_at(msg, line=line)
                self.set_leds(Keys.ALL)

            self.was_locked = is_locked

    def exit_key_message(self, msg="%(key)s key to exit", line=4, keys=Keys.ESC):
        """ A specialized version of :py:meth:`any_key_to_exit_message` for
        current state exit """
        if not isinstance(keys, (list, tuple, set)):
            keys = [keys]
        is_locked = self.is_locked()
        if self.was_locked is None or is_locked != self.was_locked:
            if is_locked:
                self.write_at(' ' * self.width, line=line)
                self.leds_off()
            else:
                self.center_text_at(msg % {'key': '-'.join([Keys.names[k] for k in keys])}, line=line)
                self.set_leds(keys)

            self.was_locked = is_locked
