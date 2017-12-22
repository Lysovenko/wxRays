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
from locale import atof
import locale as loc
try:
    type(unicode)
except NameError:
    unicode = str


class Value:
    def __init__(self, vclass):
        self.vclass = vclass
        self.value = vclass()
        self.relevance = True
        self.updater = None
        self.relevator = None

    def set_updater(self, updater):
        self.updater = updater

    def set_relevator(self, relevator):
        self.relevator = relevator

    def update(self, val, call_upd=True):
        self.value = self.vclass(val)
        if call_upd and self.updater is not None:
            self.updater(self.value)

    def get(self):
        return self.value

    def is_relevant(self, relevance=None):
        if relevance is None:
            return self.relevance
        self.relevance = bool(relevance)
        if self.relevator is not None:
            self.relevator(self.relevance)

    def __str__(self):
        return self.value.__str__()

    def __int__(self):
        return self.value.__int__()

    def __float__(self):
        return self.value.__float__()


def lfloat(noless=None, nomore=None):
    "limited float"
    if nomore is not None and noless is not None and nomore <= noless:
        raise ValueError("minimal value is more or equal than maximum")

    class efloat(float):
        def __new__(self, value=None):
            if type(value) in (str, unicode):
                value = atof(str(value))
            if value is None and noless is not None:
                value = noless
            if value is None and nomore is not None:
                value = nomore
            if noless is not None and value < noless or \
               nomore is not None and value > nomore:
                raise ValueError("value is not in range {0}:{1}".format(
                    noless, nomore))
            return float.__new__(self, value)

        def __format__(self, spec):
            return loc.format('%'+spec, self)

        def __str__(self):
            return loc.str(self)
    return efloat
