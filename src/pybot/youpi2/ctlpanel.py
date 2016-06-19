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

    class Keys(object):
        """ A symbolic representation of the panel keys """

        #: the key identifiers (TL=top-left,...)
        TL, TR, BL, BR = range(1, 5)
        #: convenience set of all keys
        ALL = (TL, TR, BL, BR)
        #: abbreviated access to the first key in the set
        FIRST = ALL[0]

        @classmethod
        def mask(cls, keys=None):
            """ Returns the port outputs mask corresponding to a given
            set of keys which LEDs should be turned on.

            The PCF outputs being used as sinks (due to very low source current capability
            of the chip), the LED are controlled with an inverted logic.

            The keys can be passed as either a single item or a set. In either case,
            values must belong to `Keys.ALL` set. If omitted, this is equivalent
            to turing all the LEDs off.

            :param keys: the set of keys to be turned on, elements being members
            of `Keys.ALL` set

            :raises TypeError: if the passed argument is not a single key or a set of key
            """
            if keys:
                try:
                    iter(keys)
                except TypeError:
                    keys = [keys]
                return ~reduce(lambda x, y: x | y, [1 << (k - 1) for k in keys]) & 0x0f
            else:
                return 0x0f

    def __init__(self, bus, debug=False):
        super(LCD05, self).__init__(bus, debug=debug)
        self.was_locked = False

    def set_leds(self, keys=None):
        """ Turns a set of LEDs on.

        .. seealso:: :py:meth:`Keys.mask` for parameter definition.
        """
        self._bus.write_byte(self.EXPANDER_ADDR, self.Keys.mask(keys) | 0xf0)

    def leds_off(self):
        """ Convenience function for turning all the LEDs off. """
        self.set_leds()

    def is_locked(self):
        """ Tells if the lock switch is on or off.

        The lock switch must be connected to P7 PCF IO, and must pull the input
        down to the ground when closed. Since the security switch used here is opened
        when the key removal position, the HIGH state corresponds to "locked".
        """
        return self._bus.read_byte(self.EXPANDER_ADDR) & 0x80

    def reset(self):
        """ Resets the panel by chaining the following operations :

        * clear the display
        * turns the back light on
        * turns the cursor display off
        * turns all the keypad LEDs off
        * set the keypad scanner of the LCD controller in fast mode
        """
        self.clear()
        self.set_backlight(True)
        self.set_cursor_type(ControlPanel.CT_INVISIBLE)
        self.leds_off()
        self.keypad_fast_scan()

    def display_splash(self, text, delay=2):
        """ Displays a page of text and waits before returning.

        If a wait is provided (as a number of seconds) the method waits
        before returning. If 0 is passed as delay, an infinite wait is done,
        which ends by pressing one of the keypad keys.

        :param str text: the lines of text, separated by newlines ('\n')
        :param int delay: the number of seconds to wait before returning.
        If 0, a key wait is used instead of a time delay.
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
        while True:
            keys = self.get_keys()
            if keys:
                k = keys.pop()
                if valid is None or k in valid:
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
            return {self.KEYPAD_3x4_KEYS.index(k) + self.Keys.FIRST for k in keys if k in self.KEYPAD_3x4_KEYS}
        else:
            return set()

    def clear_was_locked_status(self):
        self.was_locked = None

    def any_key_to_exit_message(self, msg='Any key to exit', line=4):
        """ Displays a "any key to exit" message if the panel is unlocked"""
        is_locked = self.is_locked()
        if self.was_locked is None or is_locked != self.was_locked:
            if is_locked:
                self.write_at(' ' * self.width, line=line)
                self.leds_off()
            else:
                self.center_text_at(msg, line=line)
                self.set_leds(self.Keys.ALL)

            self.was_locked = is_locked


class Menu(object):
    """ Menu definition and handling class.

    A menu is composed of a title centered on the LCD and 1 to 4 choices associated
    to the keypad keys. Choice labels are display next to their respective keys.

    Each choice is associated to a handler, which can take two forms:

    * a callable, returning a value which can be used by the application to decide what
    to do next
    * a simple value, which is then returned to the caller

    The returned value can be anything, but it is advised to use *positive* integers.
    Some specific values are predefined for representing common situations. By default,
    `Menu.BACK` (-1) means "go back to previous navigation state".
    """
    MENU_POSITIONS = {
        ControlPanel.Keys.TL: (1, 1),
        ControlPanel.Keys.BL: (4, 1),
        ControlPanel.Keys.TR: (1, 20),
        ControlPanel.Keys.BR: (4, 20),
    }

    BACK = -1

    def __init__(self, title, choices, panel):
        """
        Menu choices are specified as a dictionary, which key is the keypad key
        identifier and the value is a tuple composed of the choice label and the
        choice handler.

        :param str title: the title to be display at the LCD center
        :param dict choices: the list of choices
        :param ControlPanel panel: the control panel instance
        """
        self.title = title
        self.choices = choices
        self.panel = panel

    def display(self):
        """ Displays the menu.

        As a guidance for the user, the LEDs of the keys to which a choice as been
        associated are turned on (and only these ones).
        """
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
        """ Waits for a user choice and handles it.

        Only keys with and attached choice are taken in account. The associated
        handler (if any) is called, and its result is returned. If the handler
        of the choice is defined as a simple value, it is returned as is.

        :return: the choice handler result or the choice attached value
        """
        key = self.panel.wait_for_key(valid=self.choices.keys())
        self.panel.leds_off()
        action = self.choices[key][1]
        return action() if callable(action) else action


class Selector(object):
    """ An alternate type of menu when more than 4 total choices are needed.

    The list of choices is displayed as a spinner area, using the last line of
    the display. Bottom keys are used to move in the list of choices. Top-left
    and top-right keys are used respectively for :

    * exiting from the selector without any action
    * validating the currently displayed choice

    As in :class:`Menu`, the action attached to the selected choice is returned
    and the result is returned to the caller.

    When the escape key is used, the special value `Selector.ESC` (-1) is returned by the
    selector handler. It uses the same numerical value as `Menu.BACK` since the attached
    semantics is more or less identical.

    .. seealso:: refer to :py:class:`Menu` for method definitions
    """
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
