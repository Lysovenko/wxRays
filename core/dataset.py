# wxRays (C) 2015 Serhii Lysovenko
#
"""History of the plot"""
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


class DataSet:
    """required by Plot class"""
    def __init__(self, plots, x_label=None, y_label=None, x_units='A^{-1}'):
        self.x_label = x_label
        self.y_label = y_label
        self.x_units = x_units
        self.plots = plots
        self.fresh = True
        self.ax1 = False
        self.ax2 = False
        self.only_last = False
        self.picker = None
        self.info = None
        self.journal = Journal()
        self.tech_info = {}
        self.discards = set()
        for a in zip(*self.plots)[2]:
            if a == 1:
                self.ax1 = True
            elif a == 2:
                self.ax2 = True

    def get_units(self):
        return self.x_units

    def clone(self):
        cln = DataSet(list(self.plots), self.x_label, self.y_label, self.x_units)
        cln.picker = self.picker
        cln.tech_info.update(self.tech_info)
        cln.journal.set_parent(self.journal)
        return cln

    def append(self, plt):
        self.plots.append(plt)
        a = plt[2]
        if a == 1:
            self.ax1 = True
        elif a == 2:
            self.ax2 = True

    def replace_last(self, plt):
        """insecure replace last plot"""
        if type(plt) == tuple:
            pplt = self.plots[-1]
            self.plots[-1] = plt + pplt[len(plt):]
            self.only_last = 1
        else:
            for i, pl in enumerate(plt, len(self.plots) - len(plt)):
                pplt = self.plots[i]
                self.plots[i] = pl + pplt[len(pl):]
            self.only_last = len(plt)

    def set_picker(self, picker):
        self.picker = picker

    def set_info(self, info):
        self.info = info


class Journal(list):
    def write_to(self, fp):
        for l in self:
            fp.write("# %s\n" % l)

    def set_parent(self, parent):
        self[:0] = parent

    def log(self, msg):
        self.append(unicode(msg))

    def __str__(self):
        return "> " + "\n> ".join([unicode(i) for i in self])
