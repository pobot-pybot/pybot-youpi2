#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Curses UI based demo """

import time
from collections import namedtuple
import curses
from textwrap import dedent, fill

from pybot.core.log import uncolorify

from pybot.dspin.demo import DSPINDemo, CursesHandler
from pybot.dspin.defs import Status, Configuration
from pybot.dspin import real_raspi

from .arm.youpi6470 import YoupiArm, YoupiArmError, OutOfBoundError


__author__ = 'Eric Pascual'


MenuOption = namedtuple('MenuOption', 'selector, label, handler')


class YoupiDemo(DSPINDemo):
    """ dSPIN controlled Youpi.

    Shows various features of the daisy-chain management and Youpi specific
    features.
    """

    youpi = None

    _log_listener = None

    win_client = win_log = None
    _terminate = False

    def __init__(self, *args, **kwargs):
        super(YoupiDemo, self).__init__(*args, **kwargs)

        self.options = [
            MenuOption('O', 'seek Origins', self.seek_origin),
            MenuOption('G', 'calibrate Gripper', self.calibrate_gripper),
            None,
            MenuOption('M', 'control Motors', self.control_motors),
            MenuOption('J', 'control Joints', self.control_joints),
            None,
            MenuOption('R', 'display dSPIN Registers', self.display_registers),
            MenuOption('Z', 'Hi-Z', self.arm_hiZ),
            None,
            MenuOption('Q', 'Quit', self.terminate_demo)
        ]
        self._menu_handlers = {
            opt.selector: opt.handler for opt in self.options if opt
        }

    def _init_curses(self, win_size):
        super(YoupiDemo, self)._init_curses(win_size)
        y, x = self.win_main.getmaxyx()
        self.win_client = self._curses.newwin(y - 4, x - 4, 2, 2)
        self.win_log = self._curses.newwin(1, x - 5, y - 2, 2)
        _, w = self.win_log.getmaxyx()
        self.win_log_w = w - 1

    def get_curses_log_handler(self):
        return CursesHandler(self.win_log, curses.color_pair(curses.COLOR_BLUE))

    def setup(self):
        super(YoupiDemo, self).setup()

        self.youpi = YoupiArm(log_level=self.log.getEffectiveLevel())
        try:
            self.youpi.initialize()
        except YoupiArmError as e:
            self.log.exception(e)

    def display_menu(self):
        self.win_client.erase()
        self.win_client.addstr(0, 0, "Select an option :")
        for i, opt in enumerate(self.options):
            y = i + 2
            if opt:
                self.win_client.addstr(y, 5, "%s - %s" % (opt.selector, opt.label))
        self.win_client.refresh()

    def display_status(self, msg, color=curses.COLOR_BLUE):
        self.win_log.addnstr(0, 0, msg.strip(), self.win_log_w, curses.color_pair(color))
        self.win_log.clrtoeol()
        self.win_log.refresh()

    def success_status(self, msg="Done."):
        self.display_status(msg, curses.COLOR_GREEN)

    def error_status(self, msg):
        self.display_status(msg, curses.COLOR_RED)

    def info_status(self, msg):
        self.display_status(msg, curses.COLOR_BLUE)

    def clear_status(self):
        self.win_log.erase()
        self.win_log.refresh()

    def cannot_perform(self, wnd):
        self.error_status('Cannot perform action')

    def terminate_demo(self, wnd):
        self._terminate = True

    def selective_motor_action(self, wnd, msg, action):
        h, w = wnd.getmaxyx()

        wnd.erase()
        wnd.addstr(0, 0, fill(msg, w - 2))

        selected_attrs = curses.color_pair(curses.COLOR_GREEN)
        default_attrs = 0

        display_top = 6
        action_win = wnd.derwin(h - display_top - 2, w - 2, display_top, 0)

        error = None
        motor_num = None
        while True:
            for i, n in enumerate(self.youpi.MOTOR_NAMES):
                col = i % 3
                line = i / 3
                attrs = selected_attrs if motor_num is not None and motor_num == i else default_attrs
                wnd.addstr(line + 3, 3 + col * 25, '%d - %s' % (i + 1, n), attrs)

            if error:
                self.error_status(error)

            wnd.refresh()
            key = self.win_main.getch()

            error = None
            self.clear_status()

            action_win.erase()

            if 0 < key < 256:
                key = chr(key).upper()
                if key == 'M':
                    self.clear_status()
                    break

                try:
                    motor_num = int(key) - 1
                    if 0 <= motor_num <= 5:
                        try:
                            action(motor_num, action_win)

                        except Exception as e:
                            self.error_status(str(e))

                    else:
                        error = 'Invalid motor num'

                    continue

                except ValueError:
                    pass

                error = 'Invalid choice'

    def seek_origin(self, wnd):
        self.youpi.awake()

        def action(motor_num, wnd):
            try:
                self.info_status("Motor %s seeking its origin..." % self.youpi.MOTOR_NAMES[motor_num])
                self.youpi.seek_origin(motor_num)
            except KeyboardInterrupt:
                self.youpi.hard_hi_Z()
                self.error_status('Interrupted')
            except YoupiArmError as e:
                self.log.exception(e)
                self.error_status(str(e))
            else:
                self.success_status()

        self.selective_motor_action(
            wnd,
            "Select a motor for seeking its origin, or press 'M' key to go back to main menu :",
            action
        )

    def calibrate_gripper(self, wnd):
        self.info_status('Calibrating gripper...')
        self.youpi.calibrate_gripper()
        self.success_status()

    def display_registers(self, wnd):
        def action(motor_num, wnd):
            _, max_x = wnd.getmaxyx()

            config = self.youpi.CONFIG[motor_num]
            status = self.youpi.STATUS[motor_num]

            label_attrs = curses.color_pair(curses.COLOR_BLUE)

            wnd.addstr(0, 0, 'STATUS: ', label_attrs)
            wnd.addstr(fill(Status.as_string(status), max_x - 10))

            wnd.addstr(4, 0, 'CONFIG: ', label_attrs)
            wnd.addstr(fill(Configuration.as_string(config), max_x - 10))

            wnd.refresh()

        self.selective_motor_action(
            wnd,
            "Select a motor for displaying its registers, or press 'M' key to go back to main menu :",
            action
        )

    def control_motors(self, wnd):
        usage = """
        Control individual Youpi motors using the keyboard.

            - left/right arrows : base
            - 7, 1 : shoulder
            - 8, 2 : elbow
            - 9, 3 : wrist
            - 4, 6 : hand
            - O, C : gripper open/close

            - H : back to home position

            - M : return to main menu"""

        wnd.erase()
        for i, s in enumerate(dedent(usage.strip('\n')).split('\n')):
            wnd.addstr(i, 0, s.rstrip())

        wnd.refresh()
        error = None

        while True:
            if error:
                self.error_status(error)

            key = self.win_main.getch()

            self.clear_status()
            error = None

            try:
                if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                    self.rotate_base(wnd, key == curses.KEY_LEFT)
                else:
                    if 0 < key < 256:
                        key = chr(key).upper()
                        if key == 'M':
                            self.clear_status()
                            break
                        elif key in ('1', '7'):
                            self.actuate_shoulder(wnd, key == '7')
                        elif key in ('8', "2"):
                            self.actuate_elbow(wnd, key == '8')
                        elif key in ('9', "3"):
                            self.actuate_wrist(wnd, key == '9')
                        elif key in ('4', "6"):
                            self.rotate_hand(wnd, key == '4')
                        elif key in ('O', 'C'):
                            self.actuate_gripper(wnd, key == 'O')
                        elif key == 'H':
                            self.youpi.go_home()
                            self.success_status()
                        else:
                            error = 'Invalid key'
                    else:
                        error = 'Invalid key'

            except OutOfBoundError as e:
                error = e.message
            except KeyboardInterrupt:
                self.youpi.hard_hi_Z()

    def actuate_shoulder(self, wnd, up):
        self.actuate_motor(self.youpi.MOTOR_SHOULDER, up)

    def actuate_elbow(self, wnd, up):
        self.actuate_motor(self.youpi.MOTOR_ELBOW, up)

    def actuate_wrist(self, wnd, up):
        self.actuate_motor(self.youpi.MOTOR_WRIST, up)

    def actuate_motor(self, motor_num, up):
        self.info_status('Actuating %s motor...' % self.youpi.MOTOR_NAMES[motor_num])
        rotation_dir = 1 if up else -1
        self.youpi.joints_move({
            motor_num: 10 * rotation_dir
        })
        self.success_status()

    def rotate_hand(self, wnd, to_left):
        self.info_status('Rotating hand %s...' % ('left' if to_left else 'right'))
        rotation_dir = 1 if to_left else -1
        self.youpi.rotate_hand(10 * rotation_dir)
        self.success_status()

    def actuate_gripper(self, wnd, open_it):
        self.info_status('%s gripper...' % ('Opening' if open_it else 'Closing'))
        if open_it:
            self.youpi.open_gripper()
        else:
            self.youpi.close_gripper()
        self.success_status()

    def rotate_base(self, wnd, to_left):
        self.info_status('Rotating base %s...' % ('left' if to_left else 'right'))
        rotation_dir = 1 if to_left else -1
        self.youpi.joints_move({
            self.youpi.MOTOR_BASE: 10 * rotation_dir
        })
        self.success_status()

    def arm_hiZ(self, wnd):
        self.youpi.hard_hi_Z()
        self.success_status()

    def control_joints(self, wnd):
        usage = """
        Control Youpi joints using the keyboard.

        Depending on which joints, several motors can be involved to
        compensate the mechanical coupling of joints caused by the belts
        transmission.

            - left/right arrows : rotate base
            - 7, 1 : shoulder
            - 8, 2 : elbow
            - 9, 3 : wrist
            - 4, 6 : hand
            - O, C : gripper open/close

            - H : back to home position

            - M : return to main menu"""

        wnd.erase()
        for i, s in enumerate(dedent(usage.strip('\n')).split('\n')):
            wnd.addstr(i, 0, s.rstrip())

        wnd.refresh()
        error = None

        while True:
            if error:
                self.error_status(error)

            key = self.win_main.getch()

            self.clear_status()
            error = None

            try:
                if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                    self.rotate_base(wnd, key == curses.KEY_LEFT)
                else:
                    if 0 < key < 256:
                        key = chr(key).upper()
                        if key == 'M':
                            self.clear_status()
                            break
                        elif key in ('1', '7'):
                            self.move_shoulder(wnd, key == '7')
                        elif key in ('8', "2"):
                            self.move_elbow(wnd, key == '8')
                        elif key in ('9', "3"):
                            self.move_wrist(wnd, key == '9')
                        elif key in ('4', "6"):
                            self.rotate_hand(wnd, key == '4')
                        elif key in ('O', 'C'):
                            self.actuate_gripper(wnd, key == 'O')
                        elif key == 'H':
                            self.youpi.go_home()
                            self.success_status()
                        else:
                            error = 'Invalid key'

                    else:
                        error = 'Invalid key'

            except OutOfBoundError as e:
                error = e.message
            except KeyboardInterrupt:
                self.youpi.hard_hi_Z()

    def move_shoulder(self, wnd, up):
        self.move_joint(self.youpi.MOTOR_SHOULDER, up)

    def move_elbow(self, wnd, up):
        self.move_joint(self.youpi.MOTOR_ELBOW, up)

    def move_wrist(self, wnd, up):
        self.move_joint(self.youpi.MOTOR_WRIST, up)

    def move_joint(self, motor_num, up):
        self.info_status('Moving %s joint...' % self.youpi.MOTOR_NAMES[motor_num])
        rotation_dir = 1 if up else -1
        self.youpi.joints_move({
            motor_num: 10 * rotation_dir,
        }, coupled=True)
        self.success_status()

    def _listen_log(self):
        y, x = self.win_log.getmaxyx()
        line_len = x - 5
        while not self._terminate:
            line = self.log_stream.readline().strip()
            if line:
                self.display_status(uncolorify(line).ljust(line_len)[:line_len])

            time.sleep(0.1)

        self.log_stream.close()
        self.log.info('log listener thread ended')

    def cleanup(self, interrupted=False):
        try:
            if not interrupted:
                self.log.info('opening gripper...')
                self.youpi.open_gripper()

            self.log.info('shutting down Youpi...')
            self.youpi.shutdown()

        except Exception as e:
            self.log.exception("Unexpected error during cleanup: %s", e)

        if self._log_listener:
            self._terminate = True
            self._log_listener.join(1)

        super(YoupiDemo, self).cleanup()

    def run(self):
        youpi = self.youpi

        if youpi.ready:
            self.log.info('ready')

        else:
            self.log.error('not ready')
            self.error_status('initialization failed - no action possible')
            for key, hndlr in self._menu_handlers.items():
                if hndlr != self.terminate_demo:
                    self._menu_handlers[key] = self.cannot_perform

        while not self._terminate:
            self.display_menu()
            opt = chr(self.win_client.getch()).upper()
            try:
                self.clear_status()

                func = self._menu_handlers[opt]
                func(self.win_client)

            except KeyError:
                self.error_status('Invalid choice')


def main():
    YoupiDemo.main(use_curses=True)

if __name__ == '__main__':
    main()
