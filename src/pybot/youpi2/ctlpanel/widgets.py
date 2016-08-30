# -*- coding: utf-8 -*-

from pybot.lcd.lcd_i2c import LCD05
from pybot.youpi2.ctlpanel.keys import Keys

__author__ = 'Eric Pascual'


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
        Keys.ESC: (1, 1),
        Keys.PREVIOUS: (4, 1),
        Keys.OK: (1, 20),
        Keys.NEXT: (4, 20),
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

    def handle_choice(self):
        """ Waits for a user choice and handles it.

        Only keys with and attached choice are taken in account. The associated
        handler (if any) is called, and its result is returned. If the handler
        of the choice is defined as a simple value, it is returned as is.

        In case of interruption of the wait for key, the Interrupted exception
        will bubble up to application level.

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
    KEY_ESC = Keys.ESC
    KEY_OK = Keys.OK
    KEY_PREV = Keys.PREVIOUS
    KEY_NEXT = Keys.NEXT

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
        l = chr(LCD05.CH_CANCEL)
        l += chr(LCD05.CH_OK).rjust(self.panel.width - len(l), " ")
        self.panel.write_at(l, line=1)
        self.panel.write_at(chr(LCD05.CH_ARROW_LEFT) + ' ' * (self.panel.width - 2) + chr(LCD05.CH_ARROW_RIGHT), line=4)

    def handle_choice(self):
        while True:
            choice_descr = self.choices[self.choice]
            s = choice_descr[0][:self._w_choice]
            self.panel.write_at(s.center(self._w_choice), line=4, col=3)

            key = self.panel.wait_for_key()
            if key is None:
                return

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
