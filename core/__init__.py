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
import locale
from os.path import dirname, join, isdir
from .settings import Settings
from .addons import Addons
from .application import APPLICATION
VERSION = '0.2.1'


def install_gt():
    try:
        from gettext import install
        locale_dir = join(dirname(dirname(__file__)), 'locale')
        if isdir(locale_dir):
            install('wxRays', locale_dir, True)
        else:
            install('wxRays', unicode=True)
    except ImportError:
        try:
            __builtins__.__dict__["_"] = unicode
        except NameError:
            __builtins__.__dict__["_"] = str


def initialize():
    extvars = __builtins__
    extvars['PROG_NAME'] = "wxRays"
    APPLICATION.addons = Addons()
    APPLICATION.addons.set_active()
    locale.setlocale(locale.LC_NUMERIC, "")
    install_gt()
