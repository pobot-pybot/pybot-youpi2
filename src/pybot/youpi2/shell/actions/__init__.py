# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'


class Action(object):
    """ Root class for actions. """
    def __init__(self, panel, arm, **kwargs):
        self.panel = panel
        self.arm = arm

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def execute(self):
        raise NotImplementedError()

