#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is some interesting educational program"
# wxRays (C) 2012 Serhii Lysovenko
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import print_function, unicode_literals, absolute_import
import __builtin__
import os
from addons import Addons
import locale
from os.path import dirname, join, isdir, expanduser, normpath, isfile
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
VERSION = '0.2.1'


def install_gt():
    try:
        from gettext import install
        LOCALEDIR = join(dirname(dirname(__file__)), 'locale')
        if isdir(LOCALEDIR):
            install('wxRays', LOCALEDIR, True)
        else:
            install('wxRays', unicode=True)
    except ImportError:
        __builtin__.__dict__["_"] = unicode


class Settings:
    def __init__(self):
        self.__config = RawConfigParser()
        if os.name == 'posix':
            aphom = expanduser("~/.config")
            if isdir(aphom):
                self.__app_home = aphom + "/wxRays"
            else:
                self.__app_home = expanduser("~/.wxRays")
        elif name == 'nt':
            if isdir(expanduser("~/Application Data")):
                self.__app_home = expanduser("~/Application Data/wxRays")
            else:
                self.__app_home = expanduser("~/wxRays")
        else:
            self.__app_home = normpath(expanduser("~/wxRays"))
        if isfile(self.__app_home):
            os.remove(self.__app_home)
        if not isdir(self.__app_home):
            os.mkdir(self.__app_home, 0755)
        self.__config.read(join(self.__app_home, "wxRays.cfg"))

    def declare_section(self, section):
        if not self.__config.has_section(section):
            self.__config.add_section(section)

    def get(self, name, default=None, section='DEFAULT'):
        if not self.__config.has_option(section, name):
            return default
        deft = type(default)
        try:
            if deft == float:
                return self.__config.getfloat(section, name)
            if deft == int:
                return self.__config.getint(section, name)
            if deft == bool:
                return self.__config.getboolean(section, name)
        except ValueError:
            return default
        return self.__config.get(section, name)

    def set(self, name, val, section='DEFAULT'):
        # compensation of some stuppidness in ConfigParser with boolean
        # processing
        if type(val) == bool:
            val = str(val)
        self.__config.set(section, name, val)

    def get_home(self, name=''):
        if name:
            return join(self.__app_home, name)
        return self.__app_home

    def save(self):
        fobj = open(self.get_home("wxRays.cfg"), "w")
        self.__config.write(fobj)
        fobj.close()


def initialize():
    if 'APP_SETT' in __builtin__.__dict__:
        return
    __builtin__.__dict__['APP_SETT'] = Settings()
    __builtin__.__dict__['PROG_NAME'] = u"wxRays"
    APP_SETT.addons = Addons()
    APP_SETT.addons.set_active()
    locale.setlocale(locale.LC_NUMERIC, "")
    install_gt()


prog_init = initialize
