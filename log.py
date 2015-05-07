# wxRays (C) 2015 Serhii Lysovenko
#
"History of the plot"
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


class PlotLog(list):
    def write_to(self, fp):
        for l in self:
            fp.write("# %s\n" % l)

    def __init__(self, parent=None):
        list.__init__(self)
        if parent is not None:
            self += parent
