#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the input point to some interesting educational program"""
# wxRays (C) 2017-2018 Serhii Lysovenko
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

from importlib import import_module

from .addons import Addons
from .settings import Settings
from .menu import AppMenu
from .frameparser import Frames

_ACTUAL_INTERFACE = None


class Application:
    """container for 'global variables'"""

    def __init__(self):
        self.menu = AppMenu(self)
        self.settings = Settings()
        self.addons = Addons(self)


def start():
    global _ACTUAL_INTERFACE
    _ACTUAL_INTERFACE = import_module(".wx.face", "core")
    _ACTUAL_INTERFACE.main()


def run_dialog(user_data, xml_file, frame_name):
    f = Frames(xml_file)
    puzzle = f.get(frame_name)
    puzzle.set_data(user_data)
    return _ACTUAL_INTERFACE.run_dlg_puzzle(puzzle)


def get_progress_bar(title, message, can_abort=False):
    return _ACTUAL_INTERFACE.get_progress_bar(title, message, can_abort)


APPLICATION = Application()
