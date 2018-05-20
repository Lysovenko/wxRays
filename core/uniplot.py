#!/usr/bin/env python
#
"""Universal plot abstraction"""
# wxRays (C) 2018 Serhii Lysovenko
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
from copy import copy


class UniPlot:
    """something like core.DataSet"""
    def __init__(self, xlabel=None, ylabel=None, xunits=None):
        self.xlabel = xlabel
        self.xrange = None
        self.ylabel = ylabel
        self.yrange = None
        self.x2label = None
        self.x2range = None
        self.y2label = None
        self.y2range = None
        self.xunits = xunits
        self.yunits = None
        self.x2units = None
        self.y2units = None
        self.title = None
        self.plots = []
        self.arrows = []
        self.labels = []

    def get_units(self):
        return self.xunits, self.yunits, self.x2units, self.y2units

    def clone(self):
        return copy(self)

    def append(self, plt):
        self.plots.append(plt)


class Plot:
    def __init__(self):
        self.abscissa = None
        self.ordinate = None
        self.type = None
        self.title = None
