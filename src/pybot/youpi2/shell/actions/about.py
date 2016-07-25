# -*- coding: utf-8 -*-

from . import Action

__author__ = 'Eric Pascual'


class DisplayAbout(Action):
    version = 'none'

    def execute(self):
        self.panel.display_splash("""
        Youpi Control

        version %(version)s
        """ % {
            'version': self.version.split('+')[0]
        }, delay=2)

