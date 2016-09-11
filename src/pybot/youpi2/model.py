# -*- coding: utf-8 -*-

""" Classes implementing the models of the motors and the arm. """

import time

from pybot.dspin import defs, real_raspi, GPIO
from pybot.dspin.core import DSPinSpiDev, CommandTimeOut
from pybot.dspin.daisychain import DaisyChain
from pybot.dspin.defs import Register

from pybot.core import log

__author__ = 'Eric Pascual'


class MotorSettings(object):
    """ Base class of holder objects for the settings of a given stepper motor
    and the joint it actuates.

    It provides defaults values for the settings (refer to L6470 datasheet for
    the values documentation) and a couple of convenience methods too.

    The settings can be tuned for specific motors by sub-classing and overriding
    the required attributes.
    """
    STEPS_PER_TURN = 200    #: number of steps per motor turn
    GEAR_RATIO = 32         #: gear ratio of joint transmission
    MIN_POS_DEG = None      #: lowest position of the joint
    MAX_POS_DEG = None      #: highest position of the joint

    micro_steps = 128       #: motor micro-stepping
    max_speed = 750         #: maximum motor speed
    min_speed = 100         #: minimum motor speed
    fs_spd = 200            #: full/micro steps switching speed threshold
    acc = 0x7f              #: acceleration
    dec = 0x7f              #: deceleration
    ovd_th = defs.OverCurrentThreshold.TH_1500mA    #: over-current limit
    kval_run = 0x7f         #: constant speed phases PWM setting
    kval_acc = 0x7f         #: acceleration phases PWM setting
    kval_dec = 0x7f         #: deceleration phases PWM setting
    kval_hold = 0x0f        #: position hold phases PWM setting

    def __str__(self):
        return "STEPS_PER_TURN=%d GEAR_RATIO=%d micro_steps=%d max_speed=%d min_speed=%d fs_spd=0x%x " \
               "acc=0x%x dec=0x%x ovd_th=%s kval_run=0x%x kval_acc=0x%x kval_dec=0x%x kval_hold=0x%x " % (
            self.STEPS_PER_TURN, self.GEAR_RATIO, self.micro_steps, self.max_speed, self.min_speed,
            self.fs_spd, self.acc, self.dec, defs.OverCurrentThreshold.as_string(self.ovd_th),
            self.kval_run, self.kval_acc, self.kval_dec, self.kval_hold
        )

    def degrees_to_steps(self, deg):
        """ Converts a number of joint degrees into the equivalent motor steps, taking in account
        the motor steps per turn, the gear ratio of the joint transmission and the micro-stepping
        setting of the motor."""
        return int(deg * self.micro_steps * self.STEPS_PER_TURN * self.GEAR_RATIO / 360.)

    def steps_to_degrees(self, steps):
        """ Inverse of :py:meth:`degrees_to_steps` """
        return steps * 360. / self.micro_steps / self.STEPS_PER_TURN / self.GEAR_RATIO


class BaseMotorSettings(MotorSettings):
    """ Settings for the arm base rotation motor """
    GEAR_RATIO = 27
    MIN_POS_DEG = -180
    MAX_POS_DEG = 175

    max_speed = 600


class ShoulderMotorSettings(MotorSettings):
    """ Settings for the arm shoulder motor """
    max_speed = 500

    MIN_POS_DEG = -75
    MAX_POS_DEG = 115


class ElbowMotorSettings(MotorSettings):
    """ Settings for the arm elbow motor """
    max_speed = 500

    MIN_POS_DEG = -85
    MAX_POS_DEG = 125


class WristMotorSettings(MotorSettings):
    """ Settings for the arm wrist motor """
    max_speed = 600

    MIN_POS_DEG = -90
    MAX_POS_DEG = 115


class HandRotationMotorSettings(MotorSettings):
    """ Settings for the arm hand rotation motor.

    Even if this joint has no physical rotation limits,
    we impose logical ones for convenience."""
    max_speed = 800

    MIN_POS_DEG = -180
    MAX_POS_DEG = 180


class GripperMotorSettings(MotorSettings):
    """ Settings for the arm gripper motor.
    """
    GEAR_RATIO = 1
    micro_steps = 1

    max_speed = 2000
    ovd_th = defs.OverCurrentThreshold.TH_750mA
    kval_hold = 0
    kval_acc = 0xff
    kval_dec = 0x4f
    kval_run = 0xff

    fs_speed = max_speed / 2
    acc = 0x7ff
    dec = 0xfff

    open_speed = max_speed
    close_speed = 800

    turns = 28

    def __init__(self, **kwargs):
        """ Defines the step count for the full range open action."""
        super(GripperMotorSettings, self).__init__(**kwargs)

        self.open_steps = int(self.turns * self.STEPS_PER_TURN * self.micro_steps)


class YoupiArm(DaisyChain):
    """ The arm model is based on the daisy chain one, and defines the settings of
     its steppers.

     It provides a collection of high level methods for performing the various actions,
     including the support for the mechanical coupling of the joints, introduced by the
     architecture of the motions transmission.
     """
    DEFAULT_STANDBY_PIN = 11
    DEFAULT_BUSYN_PIN = 13

    settings = [
        BaseMotorSettings(),
        ShoulderMotorSettings(),
        ElbowMotorSettings(),
        WristMotorSettings(),
        HandRotationMotorSettings(),
        GripperMotorSettings()
    ]

    MOTORS_COUNT = len(settings)

    MOTOR_BASE, MOTOR_SHOULDER, MOTOR_ELBOW, MOTOR_WRIST, MOTOR_HAND_ROT, MOTOR_GRIPPER = \
        MOTORS_ALL = range(MOTORS_COUNT)
    MOTOR_NAMES = ['base', 'shoulder', 'elbow', 'wrist', 'hand', 'gripper']

    JOINT_CHILDREN = [None, MOTOR_ELBOW, MOTOR_WRIST, -MOTOR_HAND_ROT, None, None]
    JOINT_PARENTS = [None, None, MOTOR_SHOULDER, MOTOR_ELBOW, -MOTOR_WRIST, None]

    class TimeOuts(object):
        DEFAULT = 30,

        OPEN_GRIPPER = 10
        CLOSE_GRIPPER = 20
        CALIBRATE_GRIPPER = OPEN_GRIPPER + CLOSE_GRIPPER
        SEEK_ORIGIN = 30
        ROTATE_HAND = 30

    def __init__(self, spi_bus=0, spi_dev=0, logger=None):
        """
        :param int spi_bus: the number of the SPI bus used
        :param int spi_dev: the id of the device on the SPI bus
        :param logger: optional logger
        """
        super(YoupiArm, self).__init__(
            chain_length=self.MOTORS_COUNT,
            spi=DSPinSpiDev(spi_bus, spi_dev),
            standby_pin=self.DEFAULT_STANDBY_PIN,
            busyn_pin=self.DEFAULT_BUSYN_PIN,
            logger=logger
        )
        self.ready = False

    def configure(self, cfg):
        """ Configures the arm based on the provided data.

        :param dict cfg: configuration data
        """
        self.logger.info('loading external configuration:')
        raise NotImplementedError()
        # for m_name, m_cfg in cfg.iteritems():
        #     prefix = m_name.upper() + '_'
        #     for p_name, p_value in m_cfg.iteritems():
        #         a_name = prefix + p_name.upper()
        #         self.log.info('- %s : %s', a_name, p_value)
        #         setattr(self, a_name, p_value)

    def initialize(self):
        """ Customized initialisation of dSPIN chain. """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing initialization')
            return

        GPIO.setmode(GPIO.BOARD)

        self.logger.info('initializing daisy chain')
        try:
            if not super(YoupiArm, self).initialize():
                raise YoupiArmError('initialization failed')
        except IOError as e:
            raise YoupiArmError('IOError (check arm connection to SPI)')

        self.logger.info("applying settings")
        for i, s in enumerate(self.settings):
            self.logger.info("[%d] %s", i, s)

        self.STEP_MODE, self.MAX_SPEED, self.MIN_SPEED, self.FS_SPD, \
            self.ACC, self.DEC, self.KVAL_RUN, self.KVAL_ACC, self.KVAL_DEC, self.KVAL_HOLD \
            = zip(*(
                (
                    defs.StepMode.step_sel(s.micro_steps) | defs.StepMode.SYNC_SEL_1,
                    defs.max_spd_calc(s.max_speed),
                    defs.min_spd_calc(s.min_speed),
                    defs.fs_spd_calc(s.fs_spd),
                    s.acc,
                    s.dec,
                    s.kval_run,
                    s.kval_acc,
                    s.kval_dec,
                    s.kval_hold,
                )
                for s in self.settings
            )
        )
        self.set_config(
            oc_sd=defs.Configuration.OC_SD_DISABLE,
            sw_mode=defs.Configuration.SW_MODE_USER
        )
        self.set_lspd_opt(True)

        self.logger.info('initialization complete')
        self.ready = True
        return True

    def shutdown(self, emergency=False):
        """ Custom shutdown, putting the arm in a suitable configuration

        :param bool emergency: emergency shutdown option (don't try to act on the arm is set)
        """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing shutdown')
            return

        if not emergency:
            try:
                self.open_gripper()
            except CommandTimeOut:
                self.logger.error('timeout while waiting for gripper opening completion')

        super(YoupiArm, self).shutdown()

    def open_gripper(self, wait=True, wait_cb=None, timeout=TimeOuts.OPEN_GRIPPER):
        """ Opens the gripper.

        :param bool wait: if True, wait until the motion is complete before returning to caller
        :param wait_cb: callback function which is called at the end of the motion
        :param timeout: the maximum motion duration
        """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing open_gripper')
            return

        motors = [self.MOTOR_GRIPPER]

        self.go_home(motors, wait, wait_cb, timeout)

    def close_gripper(self, wait=True, wait_cb=None, timeout=TimeOuts.CLOSE_GRIPPER):
        """ Closes the gripper.

        The motion is automatically stopped when the object (if any) grasp is detected.

        :param bool wait: if True, wait until the motion is complete before returning to caller
        :param wait_cb: callback function which is called at the end of the motion
        :param timeout: the maximum motion duration
        """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing close_gripper')
            return

        if self.switch_is_closed[self.MOTOR_GRIPPER]:
            return

        self.go_until(*self.expand_parameters({
            self.MOTOR_GRIPPER: (
                defs.GoUntilAction.COPY,
                defs.Direction.REV,
                self.settings[self.MOTOR_GRIPPER].close_speed
            )
        }), wait=wait, wait_cb=wait_cb, timeout=timeout)

    def calibrate_gripper(self, wait=True, wait_cb=None, timeout=TimeOuts.CALIBRATE_GRIPPER):
        """ Calibrates the gripper.

        The executed sequence consists in locating the end of the close motion, then opening
        the gripper based on the configured steps count for the full motion, and finally resetting
        the position register of the motor when fully opened.

        :param bool wait: if True, wait until the motion is complete before returning to caller
        :param wait_cb: callback function which is called at the end of the motion
        :param timeout: the maximum motion duration
        """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing calibrate_gripper')
            return

        self.close_gripper()
        self.move(*self.expand_parameters({
            self.MOTOR_GRIPPER: (
                defs.Direction.FWD,
                self.settings[self.MOTOR_GRIPPER].open_steps
            )
        }), wait=wait, wait_cb=wait_cb, timeout=timeout)

        self.reset_pos([self.MOTOR_GRIPPER])

    def seek_origins(self, joint_sequence=None, timeout=TimeOuts.SEEK_ORIGIN):
        """ Moves to the origins for a list of joints.

        The motions are done in the sequence of the provided joints list.

        :param list joint_sequence: the list of involved joints
        :param timeout: the maximum motion duration
        """
        for motor in joint_sequence or range(self.MOTORS_COUNT):
            self.seek_origin(motor, timeout=timeout)

    def seek_origin(self, motor, timeout=TimeOuts.SEEK_ORIGIN):
        """ Moves a given motor to its origin and resets its position register.

        .. note:: this is not done for the gripper since it is managed differently

        :param motor: id of the involved motor
        :param timeout: the maximum motion duration
        """
        if not real_raspi:
            self.logger.warn('not on a real RasPi => bypassing seek_origin')
            return

        if motor == self.MOTOR_GRIPPER:
            return

        initial_switch_state = self.switch_is_closed[motor]

        def timeout_abort(action):
            msg = "%s %s motor origin" % (action, self.MOTOR_NAMES[motor])
            self.logger.error("time out while " + msg)
            raise CommandTimeOut(msg)

        # starts the motor in the appropriate direction to go towards the origin
        direction = defs.Direction.REV if initial_switch_state else defs.Direction.FWD
        self.run(*self.expand_parameters({
            motor: (
                direction,
                self.settings[motor].max_speed)
        }))
        # wait until the index is detected or the maximum allowed delay is expired,
        # and abort the operation in this case
        time_limit = time.time() + timeout
        try:
            while self.switch_is_closed[motor] == initial_switch_state:
                if time.time() >= time_limit:
                    timeout_abort('seeking')
                time.sleep(0.1)
        finally:
            # use a soft sop to be sure we will slight pass the index
            self.soft_stop([motor])

        # starts the motor to go back slowly to the index (we have overshot it
        # since using a soft stop previously)
        self.run(*self.expand_parameters({
            motor: (
                defs.Direction.invert(direction),
                self.settings[motor].min_speed)
        }))

        # wait until the index is detected again or the maximum allowed delay is expired,
        # and abort the operation in this case
        time_limit = time.time() + timeout
        try:
            while self.switch_is_closed[motor] != initial_switch_state:
                if time.time() >= time_limit:
                    timeout_abort('adjusting to')
                time.sleep(0.1)
        except CommandTimeOut:
            self.hard_stop([motor])
            raise

        # if here, we could complete the whole sequence successfully
        self.hard_stop([motor])
        self.reset_pos([motor])

    def rotate_hand(self, angle, wait=True, wait_cb=None, timeout=TimeOuts.ROTATE_HAND):
        """ Rotates the hand by a given angle.

        :param int angle: the rotation angle, in degrees
        :param bool wait: if True, wait until the motion is complete before returning to caller
        :param wait_cb: callback function which is called at the end of the motion
        :param timeout: the maximum motion duration
        """
        m_settings = self.settings[self.MOTOR_HAND_ROT]
        self.move(*self.expand_parameters({
            self.MOTOR_HAND_ROT: (
                defs.Direction.FWD if angle > 0 else defs.Direction.REV,
                m_settings.degrees_to_steps(angle)
            )
        }), wait=wait, wait_cb=wait_cb, timeout=timeout)

    def rotate_hand_to(self, angle, wait=True, wait_cb=None, timeout=TimeOuts.ROTATE_HAND):
        """ Rotates the hand to a given angle.

        :param int angle: the target angle, in degrees
        :param bool wait: if True, wait until the motion is complete before returning to caller
        :param wait_cb: callback function which is called at the end of the motion
        :param timeout: the maximum motion duration
        """
        m_settings = self.settings[self.MOTOR_HAND_ROT]
        self.goto(*self.expand_parameters({
            self.MOTOR_HAND_ROT: [
                m_settings.degrees_to_steps(angle)
            ]
        }), wait=wait, wait_cb=wait_cb, timeout=timeout)

    @staticmethod
    def _normalize_angles_parameter(angles):
        """ Ensures the angles are specified as a dictionary keyed by the joint identifier.

        :param angles: a dict or equivalent list of tuples (joint_id, angle)
        :return: the dict of (joint: angle)
        """
        if isinstance(angles, (list, tuple)):
            return dict(angles)
        elif not isinstance(angles, dict):
            raise TypeError('angles parameter is not a dict or a compatible format')
        return angles

    @classmethod
    def _apply_coupling(cls, angles):
        """ Applies the compensation for joints mechanical coupling.

        The passed angle set points dictionary is modified in place

        .. Note::

            The iteration and test seem a bit C-ish, since it does not use
            iteration on a key view, but this is on purpose. We need to iterate over the
            sorted list of motors because of the way joints are coupled. Iterating over
            keys does not ensure this order.

        :param dict angles: the angles set points for involved motors
        """
        for m in reversed(cls.MOTORS_ALL):
            if m in angles:
                m_angle = angles[m]
                child = cls.JOINT_CHILDREN[m]
                while child is not None:
                    c_dir = -1 if child < 0 else +1
                    child = abs(child)
                    angles[child] = (angles[child] + c_dir * m_angle) if child in angles else c_dir * m_angle
                    child = cls.JOINT_CHILDREN[child]

    @classmethod
    def _global_to_local(cls, angles):
        """ Converts joint angles to their relative (aka local) value.

        :param list angles: the angles to convert
        :return: the corresponding local values
        :rtype: list
        """
        local_angles = angles[:]
        for j, a in enumerate(angles):
            parent = cls.JOINT_PARENTS[j]
            if parent is not None:
                c_dir = -1 if parent < 0 else +1
                parent = abs(parent)
                local_angles[j] = a - angles[parent] * c_dir

        return local_angles

    def _check_limits(self, angles, rel_move):
        """ Checks if the passed angle goals are compatible with the mechanical
        constraints of the arm.

        :param dict angles: the joint angle goals
        :param bool rel_move: True if the move is a relative one
        :raise: OutOfBoundError if the requested move would push one of more joints outside of
        its limits
        """
        # compute the final positions, depending on the kind of move (absolute or relative)
        abs_pos_regs = self.read_register(Register.ABS_POS)
        if self.logger.getEffectiveLevel() == log.DEBUG:
            self.logger.debug('_check_limits: abs_pos_regs=%s', abs_pos_regs)
        if rel_move:
            goals = [
                self.settings[j].steps_to_degrees(cur_steps) + angles.get(j, 0)
                for j, cur_steps in enumerate(abs_pos_regs)
            ]
        else:
            goals = [
                self.settings[j].steps_to_degrees(cur_steps) + angles.get(j, 0)
                for j, cur_steps in enumerate(abs_pos_regs)
            ]
            for j, a in angles.iteritems():
                goals[j] = a

        local_angles = self._global_to_local(goals)
        if self.logger.getEffectiveLevel() == log.DEBUG:
            self.logger.debug('_check_limits: glb=%s loc=%s)', goals, local_angles)

        # check the limits now
        for motor in range(self.MOTOR_BASE, self.MOTOR_HAND_ROT):
            settings = self.settings[motor]
            angle = local_angles[motor]
            if not settings.MIN_POS_DEG <= angle <= settings.MAX_POS_DEG:
                raise OutOfBoundError("%s goal (%f) out of bounds" % (self.MOTOR_NAMES[motor], angle))

    def joints_move(self, angles, wait=True, wait_cb=None, coupled=False, timeout=TimeOuts.DEFAULT):
        """ Moves joints, either as independent motors or as mechanically coupled joints.

        In coupled mode, the real commands applied to the motors will take the coupling
        of the joints in account to compute the compensations to be applied to the other
        motors so that the final position of the relevant joint is the one requested.

        In non coupled mode, the commands are computed regardless the motion of the other
        motors. Because of the coupling, a joint can have its position modified even if
        no command is set for it, but as a consequence of the move of previous motors
        in the coupling chain.

        :param dict angles: a (joint->angle) dict or the equivalent tuples list
        :param bool wait: True if blocking call
        :param wait_cb: an optional callback o be invoked while waiting in blocking mode
        :param bool coupled: True for taking the coupling in account (default: False)
        :param timeout: the maximum motion duration

        :raise: OutOfBoundError if the requested move would push one of more joints outside of
                their limits
        """
        angles = self._normalize_angles_parameter(angles)

        if coupled:
            self._apply_coupling(angles)

        self._check_limits(angles, rel_move=True)

        parms = self.expand_parameters({
            m: [
                defs.Direction.FWD if a > 0 else defs.Direction.REV,
                self.settings[m].degrees_to_steps(a)
            ]
            for m, a in angles.iteritems()
        })

        self.move(*parms, wait=wait, wait_cb=wait_cb, timeout=timeout)

    def coupled_joints_move(self, angles, wait=True, wait_cb=None, timeout=TimeOuts.DEFAULT):
        """ Shorthand for applying the coupling to a relative move.
        """
        return self.joints_move(angles, wait=wait, wait_cb=wait_cb, coupled=True, timeout=timeout)

    def joints_goto(self, angles, wait=True, wait_cb=None, coupled=False, timeout=TimeOuts.DEFAULT):
        """ Same as :py:meth:`joints_move` but for an absolute move
        """
        angles = self._normalize_angles_parameter(angles)
        if coupled:
            self._apply_coupling(angles)
        self._check_limits(angles, rel_move=False)
        parms = self.expand_parameters({
            m: [self.settings[m].degrees_to_steps(a)]
            for m, a in angles.iteritems()
        })
        self.goto(*parms, wait=wait, wait_cb=wait_cb, timeout=timeout)

    def coupled_joints_goto(self, angles, wait=True, wait_cb=None, timeout=TimeOuts.DEFAULT):
        """ Shorthand for applying the coupling to an absolute move.

        Using this method with result in the arm joints having the position specified
        in the parameters at the end of the motion.
        """
        return self.joints_goto(angles, wait=wait, wait_cb=wait_cb, coupled=True, timeout=timeout)

    def get_joint_positions(self):
        """ Returns the current position (in degrees) of the arm joints.

        Positions are returned as an array, which index is the joint motor id.

        :return: current joint positions
        :rtype: array
        """
        return [self.settings[m].steps_to_degrees(s) for m, s in enumerate(self.ABS_POS)]


class YoupiArmError(Exception):
    pass


class OutOfBoundError(YoupiArmError):
    pass
