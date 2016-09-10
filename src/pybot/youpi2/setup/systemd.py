# -*- coding: utf-8 -*-

import pbsystemd.helpers

__author__ = 'Eric Pascual'

SERVICE_NAME = 'youpi2-shell'


def install_service():
    pbsystemd.helpers.install_unit(SERVICE_NAME, __name__)


def remove_service():
    pbsystemd.helpers.remove_unit(SERVICE_NAME, __name__)
