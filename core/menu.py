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
        """adds an item to the menu"""
        if not path:
            path = ()
        holder = self.menu_items
        numpath = []
        for iname in path:
            for pos, mi in enumerate(holder):
                if mi.name == iname:
                    holder = mi.function
                    numpath.append(pos)
                    break
        holder.append(MenuItem(name, title, function, description, icon))
        adder = self.handlers.get("add_item")
        if adder:
            adder(numpath, title, function, description, icon)
        return numpath

    def remove_item(self, path):
        """removes an item from the menu"""
        if not path:
            return
        item = self.menu_items
        numpath = []
        for iname in path:
            for pos, mi in enumerate(item):
                if mi.name == iname:
                    item = mi.function
                    numpath.append(pos)
                    break
        if type(item.function) is list:
            for mi in item.function:
                self.remove_item(tuple(path)+(mi.name,))
        remover = self.handlers.get("remove_item")
        if remover:
            remover(numpath)
        #delete me somehow
