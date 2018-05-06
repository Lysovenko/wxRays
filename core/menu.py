#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Menu abstraction"""
# wxRays (C) 2019 Serhii Lysovenko
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
from weakref import ref
from collections import namedtuple


MenuItem = namedtuple("MenuItem",
                      ["name", "title", "function", "description", "icon"])


class AppMenu:
    def __init__(self, app):
        self.application = ref(app)
        self.menu_items = []
        self.act_history = []
        self.act_catchers = []
        self.handlers = dict()

    def add_item(self, path, name, title, function,
                 description=None, icon=None):
        if not path:
            self.menu_items.append(
                MenuItem(name, title, function, description, icon))
            return
        holder = self.menu_items
        for i in path:
            for mi in holder:
                if mi.name == i:
                    holder = mi.function
