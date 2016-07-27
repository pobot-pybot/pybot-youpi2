# -*- coding: utf-8 -*-

from pybot.core import log

__author__ = 'Eric Pascual'


class Action(object):
    """ Root class for actions. """
    def __init__(self, panel, arm, **kwargs):
        self.panel = panel
        self.arm = arm
        self.logger = log.getLogger(self.__class__.__name__)

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def execute(self):
        raise NotImplementedError()

