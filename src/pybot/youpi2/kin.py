# -*- coding: utf-8 -*-

import math

from pybot.core.log import LogMixin

from model import YoupiArm

__author__ = 'Eric Pascual'


class Kinematics(LogMixin):
    L_SEGMENT = 162
    L_GRIPPER = 150
    Z_SHOULDER = 280
    BASE_RADIUS = 100
    X_OFFSET_FROM_ROTATION_AXIS = 105

    def __init__(self, *args, **kwargs):
        LogMixin.__init__(self, *args, **kwargs)

    def ik(self, x, y, z, wrist_pitch=90):
        """ Inverse kinematics.

        Returns the pose corresponding to the goal gripper end cartesian position,
        with the provided wrist absolute pitch.

        The reference frame for the coordinates is defined as follows:

        * XY plane at "table" level (i.e. 280 mm down the shoulder joint)
        * X axis same as Youpi enclosure main axis
        * positive X away from front face (i.e. control panel one)
        * X origin at front face level (more or less 105 mm from the base rotation axis)
        * Z axis parallel to the base rotation one
        * positive Z upwards
        * Y axes oriented to form a direct frame, i.e. positive Y rightwards when facing the
           control panel

        Coordinate units are expressed in millimeters.

        The wrist pitch is provided in degrees, 0 being horizontal, positive angles counted
        clockwise.

        The pose is returned as a tuple, containing the joint angles, in the sequence
        base, shoulder, elbow and wrist.

        :param float x: X coordinate of the gripper end
        :param float y: Y coordinate of the gripper end
        :param float z: Z coordinate of the gripper end
        :param float wrist_pitch: absolute pitch of the gripper
        :return: arm pose as the tuple of the joint angles
        :rtype: tuple
        :raise ValueError: if the goal position cannot be reached (including the wrist pitch constraint)
        """
        input_parms_msg = 'goal: x=%f y=%f z=%f wrist_pitch=%f' % (x, y, z, wrist_pitch)
        self.log_debug(input_parms_msg)

        q_min_max = [
            (YoupiArm.motor_name(m_id), (settings.MIN_POS_DEG, settings.MAX_POS_DEG))
            for m_id, settings in enumerate(YoupiArm.settings)
        ]

        # move to shoulder related frame (translated to shoulder rotation axis center)
        z_rel = z - self.Z_SHOULDER
        x_rel = x + self.X_OFFSET_FROM_ROTATION_AXIS

        r = math.sqrt(x_rel * x_rel + y * y)
        self.log_debug('... r=%f' % r)
        base_angle = math.acos(x_rel / r) * (1 if y > 0 else -1)

        wrist_rd = math.radians(wrist_pitch)
        r_wrist = r - self.L_GRIPPER * math.cos(wrist_rd)
        z_wrist = z_rel + self.L_GRIPPER * math.sin(wrist_rd)       # Z wrist relative to the shoulder joint
        self.log_debug('... wrist relative position: r=%f z=%f' % (r_wrist, z_wrist + self.Z_SHOULDER))

        d = math.sqrt(r_wrist * r_wrist + z_wrist * z_wrist)
        if d > 2 * self.L_SEGMENT:
            msg = 'out of reach goal'
            self.log_error(msg)
            self.log_error(input_parms_msg)
            raise ValueError(msg)

        a0 = math.acos(r_wrist / d) * (1 if z_wrist >= 0 else -1)
        a1 = math.acos(d / 2 / self.L_SEGMENT)
        shoulder_angle = math.pi / 2 - a0 - a1
        elbow_angle = 2 * a1
        wrist_angle = math.pi / 2 + wrist_rd - shoulder_angle - elbow_angle

        q = [base_angle, shoulder_angle, elbow_angle, wrist_angle] = \
            [math.degrees(a) for a in (base_angle, shoulder_angle, elbow_angle, wrist_angle)]

        self.log_debug('... base: %f' % base_angle)
        self.log_debug('... shoulder: %f' % shoulder_angle)
        self.log_debug('... elbow: %f' % elbow_angle)
        self.log_debug('... wrist: %f' % wrist_angle)

        limit_errors = []
        for a, limit in zip(q, q_min_max):
            which, min_max = limit
            if not min_max[0] <= a <= min_max[1]:
                limit_errors.append(which)

        if limit_errors:
            msg = 'mechanical limits (%s)' % ','.join(limit_errors)
            self.log_error(msg)
            self.log_error(input_parms_msg)
            raise ValueError(msg)

        self.log_debug('>>> solution is valid')
        return q

    def dk(self, pose):
        """ Direct kinematics.

        Returns the gripper end 3D coordinates corresponding to a pose.

        Only the first 4 joints (i.e. base to wrist) are taken in account from the provided
        pose. So this one can be reduced to them.

        :param iterable pose: joint angles, in the sequence of motor ids
        :return: 3D coordinates of the gripper end
        :rtype: tuple
        """
        base, shoulder, elbow, wrist = (math.radians(a) for a in pose[:4])
        r = self.L_SEGMENT * math.sin(shoulder) \
            + self.L_SEGMENT * math.sin(shoulder + elbow) \
            + self.L_GRIPPER * math.sin(shoulder + elbow + wrist)
        z = self.Z_SHOULDER + \
            self.L_SEGMENT * math.cos(shoulder) \
            + self.L_SEGMENT * math.cos(shoulder + elbow) \
            + self.L_GRIPPER * math.cos(shoulder + elbow + wrist)
        y = -r * math.sin(base)
        x = r * math.cos(base) - self.X_OFFSET_FROM_ROTATION_AXIS

        return x, y, z
