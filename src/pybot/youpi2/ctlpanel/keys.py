# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'


class Keys(object):
    """ A symbolic representation of the panel keys """

    #: the key identifiers (top-left=ESC, top-right=OK, bottom-left=PREVIOUS, bottom-right=NEXT)
    ESC, OK, PREVIOUS, NEXT = range(1, 5)
    #: convenience set of all keys
    ALL = (ESC, OK, PREVIOUS, NEXT)
    #: abbreviated access to the first key in the set
    FIRST = ALL[0]
    #: key names
    names = {
        ESC: 'ESC',
        OK: 'OK',
        PREVIOUS: 'PREV',
        NEXT: 'NEXT'
    }

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

