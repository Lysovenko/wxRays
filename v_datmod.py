#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Visual data modifier"
# wxRays (C) 2014 Serhii Lysovenko
#
# This program is free software; you can redistribute it and / or modify
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.


from v_plot import plot_exp_data
from v_dialogs import v_input


class VDM_menu:
    def __init__(self, data, callback):
        self.data = data
        self.__call__ = getattr(self, callback)

    def crop_data(self, evt):
        dat = self.data
        tfn = _("Intensity curve")
        plot = dat['plot']
        if plot.get_cur_key() != tfn:
            plot.plot_dataset(tfn)
            return
        edat = dat['data'].get("Exp. data")
        if edat is None:
            return
        x = edat.x_data
        beg, end = plot.axes1.get_xbound()
        bi = 0
        lx = len(x)
        while bi < lx and x[bi] < beg:
            bi += 1
        ei = lx - 1
        while x[ei] > end and ei > 0:
            ei -= 1
        ei += 1
        if ei - bi <= 0:
            return
        edat.x_data = edat.x_data[bi:ei]
        edat.y_data = edat.y_data[bi:ei]
        plot_exp_data(plot, edat, dat['menu'])

    def shift_data(self, evt):
        dat = self.data
        tfn = _("Intensity curve")
        plot = dat['plot']
        if plot.get_cur_key() != tfn:
            plot.plot_dataset(tfn)
            return
        x_sh = _("Shift X by:"), 0.
        y_sh = _("Shift Y by:"), 0.
        rv = v_input(dat["window"], _("Shift data"), x_sh, y_sh)
        if rv is None:
            return
        x_sh, y_sh = rv
        edat = dat['data'].get("Exp. data")
        if edat is None:
            return
        if x_sh != 0.:
            edat.x_data += x_sh
        if y_sh != 0.:
            edat.y_data += y_sh
        plot_exp_data(plot, edat, dat['menu'])
