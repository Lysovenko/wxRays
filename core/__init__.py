#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is the input point to some interesting educational program"
# wxRays (C) 2017 Serhii Lysovenko
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

from __future__ import absolute_import, division, unicode_literals
import __builtin__
import locale
from os.path import dirname, join, isdir
from .settings import Settings
from .addons import Addons
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
        try:
            __builtin__.__dict__["_"] = unicode
        except NameError:
            __builtin__.__dict__["_"] = str


def initialize():
    if 'APP_SETT' in __builtin__.__dict__:
        return
    __builtin__.__dict__['APP_SETT'] = Settings()
    __builtin__.__dict__['PROG_NAME'] = "wxRays"
    APP_SETT.addons = Addons()
    APP_SETT.addons.set_active()
    locale.setlocale(locale.LC_NUMERIC, "")
    install_gt()
