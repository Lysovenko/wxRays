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


MenuItem = namedtuple("MenuItem", [
    "name", "title", "function", "shortcut", "description", "icon"])


class AppMenu:
    def __init__(self, app):
        self.application = ref(app)
        self.menu_items = []
        self.act_history = []
        self.act_catchers = []
        self.handlers = dict()

    def get_numeric_path(self, path, level=1):
        """get numeric path and last holders one"""
        if not path:
            path = ()
        holders = [self.menu_items]
        numpath = []
        for iname in path:
            for pos, mi in enumerate(holders[-1]):
                if mi.name == iname:
                    holders.append(mi.function)
                    numpath.append(pos)
                    break
        return numpath, holders[-level]

    def append_item(self, path, name, title, function, shortcut,
                 description=None, icon=None):
        """appends an item to the menu"""
        numpath, holder = self.get_numeric_path(path)
        holder.append(MenuItem(name, title, function, shortcut,
                               description, icon))
        appender = self.handlers.get("append_item")
        if appender:
            appender(numpath, title, function, shortcut, description, icon)
        return numpath

    def insert_item(self, path, position, name, title, function, shortcut,
                 description=None, icon=None):
        """inserts an item to the menu"""
        numpath, holder = self.get_numeric_path(path)
        holder.insert(position, MenuItem(name, title, function, shortcut,
                               description, icon))
        inserter = self.handlers.get("insert_item")
        if inserter:
            inserter(numpath, position, title, function, shortcut,
                     description, icon)
        return numpath

    def insert_item_relative(self, path, rel_pos, name, title, function,
                             shortcut, description=None, icon=None):
        """inserts an item to the menu relative to the path"""
        numpath, holder = self.get_numeric_path(path, 2)
        position = numpath[-1] + rel_pos
        numpath = numpath[:-1]
        holder.insert(position, MenuItem(name, title, function, shortcut,
                               description, icon))
        inserter = self.handlers.get("insert_item")
        if inserter:
            inserter(numpath, position, title, function, shortcut,
                     description, icon)
        return numpath

    def insert_item_after(self, path, name, title, function,
                             shortcut, description=None, icon=None):
        """inserts an item to the menu after the appointed item"""
        return self.insert_item_relative(path, name, 1, title, function,
                                         shortcut, description, icon)

    def insert_item_before(self, path, name, title, function,
                             shortcut, description=None, icon=None):
        """inserts an item to the menu before the appointed item"""
        return self.insert_item_relative(path, name, 0, title, function,
                                         shortcut, description, icon)

    def remove_item(self, path):
        """removes an item from the menu"""
        if not path:
            return
        tholder = self.menu_items
        numpath = []
        for iname in path:
            for pos, mi in enumerate(tholder):
                if mi.name == iname:
                    item = mi
                    iholder = tholder
                    tholder = item.function
                    numpath.append(pos)
                    break
        if type(tholder) is list:
            for mi in tholder:
                self.remove_item(tuple(path)+(mi.name,))
        remover = self.handlers.get("remove_item")
        if remover:
            remover(numpath)
        iholder.remove(item)
