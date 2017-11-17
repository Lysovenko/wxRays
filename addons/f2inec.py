#!/usr/bin/env python
# -*- coding: utf-8 -*-
"f2inec.py"
# wxRays (C) 2013 Serhii Lysovenko
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

from marshal import load
import os.path as osp
import numpy as np
from scipy.interpolate import interp1d


def get_f2i_dict():
    nam = osp.join(osp.dirname(__file__), 'af.dmp')
    with open(nam, 'rb') as fp:
        res = load(fp)
    return res


def f2_calc(f2i, xarr, lmnts):
    res = xarr * 0.
    for ei, ni in lmnts:
        f_0 = np.array(f2i[ei]["f_0"])
        f2 = (f_0 + f2i[ei]["f'"]) ** 2 + f2i[ei]["f''"] ** 2
        S = np.array(f2i[ei]["S"])
        f2_in = interp1d(S, f2, kind='cubic')
        res += f2_in(xarr) * ni
    return res


def inec_calc(f2i, xarr, lmnts):
    res = xarr * 0.
    for ei, ni in lmnts:
        I_c = np.array(f2i[ei]["I_compt"])
        S = np.array(f2i[ei]["S"])
        I_c_in = interp1d(S, I_c, kind='cubic')
        res += I_c_in(xarr) * ni
    return res


if __name__ == '__main__':
    import __builtin__
    import settings
    __builtin__.__dict__['APP_SETT'] = settings.Settings()
    print('hello f2inec')
