import unittest

from pybot.youpi2.model import YoupiArm


class JointToMotorTestCase(unittest.TestCase):
    def test_01(self):
        angles = {
            YoupiArm.MOTOR_BASE: 10
        }
        angles_orig = angles.copy()

        YoupiArm.joint_to_motor(angles)

        self.assertDictEqual(angles, angles_orig)

    def test_02(self):
        angles = {
            YoupiArm.MOTOR_BASE: 0,
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 0,
            YoupiArm.MOTOR_WRIST: 0,
            YoupiArm.MOTOR_HAND_ROT: 0,
        }

        YoupiArm.joint_to_motor(angles)

        self.assertDictEqual(angles, {
            YoupiArm.MOTOR_BASE: 0,
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 10,
            YoupiArm.MOTOR_WRIST: 10,
            YoupiArm.MOTOR_HAND_ROT: -10,
        })


class MotorToJointTestCase(unittest.TestCase):
    def test_01(self):
        angles = {
            YoupiArm.MOTOR_BASE: 10
        }
        angles_orig = angles.copy()

        YoupiArm.motor_to_joint(angles)

        self.assertDictEqual(angles, angles_orig)

    def test_02(self):
        angles = {
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 10,
            YoupiArm.MOTOR_WRIST: 10,
            YoupiArm.MOTOR_HAND_ROT: -10,
        }

        YoupiArm.motor_to_joint(angles)

        self.assertDictEqual(angles, {
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 0,
            YoupiArm.MOTOR_WRIST: 0,
            YoupiArm.MOTOR_HAND_ROT: 0,
        })

    def test_03(self):
        angles = {
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 20,
            YoupiArm.MOTOR_WRIST: 30,
            YoupiArm.MOTOR_HAND_ROT: -50,
        }

        YoupiArm.motor_to_joint(angles)

        self.assertDictEqual(angles, {
            YoupiArm.MOTOR_SHOULDER: 10,
            YoupiArm.MOTOR_ELBOW: 10,
            YoupiArm.MOTOR_WRIST: 10,
            YoupiArm.MOTOR_HAND_ROT: -20,
        })


if __name__ == '__main__':
    unittest.main()
