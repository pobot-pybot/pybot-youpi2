# -*- coding: utf-8 -*-

import unittest

from pybot.core import log
from pybot.youpi2.kin import Kinematics

__author__ = 'Eric Pascual'

log.logging.basicConfig(
    format="%(msg)s"
)
logger = log.getLogger()


class IKTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kin = Kinematics(parent=logger)
        cls.kin.log_setLevel(log.DEBUG)

    def test_01(self):
        q = self.kin.ik(
            2 * Kinematics.L_SEGMENT + Kinematics.L_GRIPPER - Kinematics.X_OFFSET_FROM_ROTATION_AXIS,
            0,
            Kinematics.Z_SHOULDER,
            0
        )
        for angle, expected in zip(q, [0.0, 90.0, 0.0, 0.0]):
            self.assertAlmostEqual(angle, expected, places=1)

    def test_02(self):
        q = self.kin.ik(
            Kinematics.L_SEGMENT - Kinematics.X_OFFSET_FROM_ROTATION_AXIS,
            0,
            Kinematics.Z_SHOULDER - Kinematics.L_SEGMENT - Kinematics.L_GRIPPER,
            90
        )
        for angle, expected in zip(q, [0.0, 90.0, 90.0, 0.0]):
            self.assertAlmostEqual(angle, expected, places=1)

    def test_03(self):
        q = self.kin.ik(Kinematics.L_SEGMENT - Kinematics.X_OFFSET_FROM_ROTATION_AXIS, 0, 0, 90)
        for angle, expected in zip(q, [0.0, 78.6, 100.25, 1.1]):
            self.assertAlmostEqual(angle, expected, places=1)

    def test_04(self):
        with self.assertRaises(ValueError):
            self.kin.ik(Kinematics.L_SEGMENT, 0, 0, 0)

    def test_05(self):
        with self.assertRaises(ValueError):
            self.kin.ik(-2 * Kinematics.L_SEGMENT - Kinematics.L_GRIPPER, 0, Kinematics.Z_SHOULDER, 0)

    def test_06(self):
        q = self.kin.ik(
            Kinematics.L_SEGMENT + Kinematics.L_GRIPPER - Kinematics.X_OFFSET_FROM_ROTATION_AXIS,
            Kinematics.L_SEGMENT,
            Kinematics.Z_SHOULDER,
            0
        )
        for angle, expected in zip(q, [27.4, 38.5, 103.1, -51.5]):
            self.assertAlmostEqual(angle, expected, places=1)


class DKTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kin = Kinematics(parent=logger)
        cls.kin.log_setLevel(log.DEBUG)

    def test_01(self):
        xzy = self.kin.dk((0, 0, 0, 0))
        self.assertTupleEqual(xzy, (
            -Kinematics.X_OFFSET_FROM_ROTATION_AXIS,
            0,
            Kinematics.Z_SHOULDER + 2 * Kinematics.L_SEGMENT + Kinematics.L_GRIPPER
        ))

    def test_02(self):
        xzy = self.kin.dk((0, 90, 0, 90))
        self.assertTupleEqual(xzy, (
            2 * Kinematics.L_SEGMENT - Kinematics.X_OFFSET_FROM_ROTATION_AXIS,
            0,
            Kinematics.Z_SHOULDER - Kinematics.L_GRIPPER
        ))


if __name__ == '__main__':
    unittest.main()
