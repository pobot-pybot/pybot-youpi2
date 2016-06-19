# -*- coding: utf-8 -*-

import subprocess

from . import Action

__author__ = 'Eric Pascual'


class ManualControl(Action):
    def execute(self):
        subprocess.call(['top'])


