#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pybot.lcd.lcd_i2c import LCD05

__author__ = 'Eric Pascual'


class LCDPanel(LCD05):
    EXPANDER_ADDR = 0x20

    TL_KEY = '1'
    TR_KEY = '2'
    BL_KEY = '4'
    BR_KEY = '5'

    def __init__(self, bus, debug=False):
        super(LCD05, self).__init__(bus, debug=debug)

    def set_leds(self, keys=None):
        if keys:
            self._bus.write_byte_data(
                self.EXPANDER_ADDR,
                0,
                ~reduce(lambda x, y: x | y, ['1245'.index(k) for k in keys])
            )
        else:
            self._bus.write_byte_data(self.EXPANDER_ADDR, 0, 0x0f)
