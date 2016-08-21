# -*- coding: utf-8 -*-

""" This module provides classes for managing Youpi's control panel.

The version of the :py:class:`ControlPanel` class defined in this module
offers functionality similar as the one in the `direct` sibling module,
but works with the virtual file system interface instead of the I2C
direct access.

It thus requires that the `lcdfs` FUSE file system is available on the
system.
"""

import os
import threading

__author__ = 'Eric Pascual'


class FileSystemDevice(object):
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
        F_KEYS: False,
        F_DISPLAY: True,
        F_INFO: False,
        F_CONTRAST: True,
        F_BRIGHTNESS: True,
        F_LEDS: True,
        F_LOCKED: False,
    }

    KEYPAD_SCAN_PERIOD = 0.1

    def __init__(self, mount_point, debug=False):
        """
        :param str mount_point: the path of the mount point where the panel FUSE file system is mounted
        :param bool debug: activates the debug mode
        """
        if not os.path.isdir(mount_point):
            raise ValueError('mount point not found : %s' % mount_point)

        self._debug = debug

        self.was_locked = False

        self._mount_point = mount_point
        self._fs_files = {
            n: open(os.path.join(mount_point, n), 'r+' if self._READ_WRITE[n] else 'r')
            for n in os.listdir(mount_point)
        }

        self._info = {}
        for line in self._fs_files[self.F_INFO]:
            attr, value = (j.strip() for j in line.split(':'))
            try:
                value = int(value)
            except ValueError:
                pass
            self._info[attr] = value
        self._width = self._info['cols']
        self._height = self._info['rows']

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def _fp(self, name):
        try:
            fp = self._fs_files[name]
            fp.seek(0)
            return fp
        except KeyError:
            raise TypeError("not supported")

    def get_leds_state(self):
        return int(self._fp(self.F_LEDS).read())

    def set_leds_state(self, state):
        fp = self._fp(self.F_LEDS)
        fp.write(str(state))
        fp.flush()

    def is_locked(self):
        """ Tells if the lock switch is on or off.
        """
        return bool(int(self._fp(self.F_LOCKED).read()))

    def get_backlight(self):
        return bool(int(self._fp(self.F_BACKLIGHT).read()))

    def set_backlight(self, on):
        fp = self._fp(self.F_BACKLIGHT)
        fp.write('1' if on else '0')
        fp.flush()

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
        self.set_leds_state(0)

    def clear(self):
        fp = self._fp(self.F_DISPLAY)
        fp.write('\x0c')
        fp.flush()

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
        fp = self._fp(self.F_DISPLAY)
        fp.write(s)
        fp.flush()

    def get_keypad_state(self):
        # handle potential race concurrency by retaining the latest information
        raw = self._fp(self.F_KEYS).read().strip()
        try:
            return int(raw.split('\n')[-1])
        except ValueError:
            # handle possible invalid data
            return 0
