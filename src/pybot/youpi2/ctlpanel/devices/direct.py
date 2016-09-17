# -*- coding: utf-8 -*-

""" This module provides classes for managing Youpi's control panel.

The control panel is composed of a LCD05 4x20 LCD display, associated to
a reduced matrix keypad (2x2 keys). LEDs are integrated in the key buttons
and can be controlled by software.

Both the LCD and the LEDs use I2C to communicate, the LEDs being driven
by an I2C IO expander (PCF8574).

The version of the :py:class:`ControlPanel` class defined in this module
uses a direct access to the panel via the I2C bus.
"""

from evdev import ecodes

from pybot.lcd.lcd_i2c import LCD05

from ..keys import Keys

__author__ = 'Eric Pascual'


class ControlPanelDevice(LCD05):
    """ Low level interface of the control panel device, using direct I2C bus access.

    It provides also a modified view of the keypad, replacing the identification
    of the keys by the digits printed on their faces by their position (top-left,
    top-right,...).

    It is implemented as an extended version of the LCD05 driver class, adding methods for
    control the key LEDs and checking the lock switch.
    """

    EXPANDER_ADDR = 0x20

    def __init__(self, bus, debug=False):
        super(LCD05, self).__init__(bus, debug=debug)
        self.was_locked = False

    def get_leds_state(self):
        port_state = self._bus.read_byte(self.EXPANDER_ADDR)
        return ~port_state & 0x0f

    def set_leds_state(self, state):
        # Remember we work in inverted logic at expander level, since connected
        # in sink mode => invert the LED states to obtain the port ones.
        port_state = ~state
        # Take care also to set other IOs as inputs (0xf0 mask)
        self._bus.write_byte(self.EXPANDER_ADDR, port_state | 0xf0)

    def set_leds(self, keys=None):
        """ Turns a set of LEDs on.

        .. seealso:: :py:meth:`Keys.mask` for parameter definition.
        """
        self.set_leds_state(Keys.mask(keys))

    def leds_off(self):
        """ Convenience function for turning all the LEDs off. """
        self.set_leds_state(0)

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
        self.leds_off()
        super(ControlPanelDevice, self).reset()

    @staticmethod
    def get_keypad_map():
        keypad_map = [None] * 12

        keypad_map[0] = ecodes.KEY_ESC
        keypad_map[1] = ecodes.KEY_OK
        keypad_map[3] = ecodes.KEY_PREVIOUS
        keypad_map[4] = ecodes.KEY_NEXT

        return keypad_map

    def get_version(self):
        return 'LCD05-%s' % super(ControlPanelDevice, self).get_version()
