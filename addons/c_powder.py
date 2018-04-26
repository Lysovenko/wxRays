#!/usr/bin/env python
# -*- coding: utf-8 -*-
"c_powder.py powder diffractograms treatment"
# wxRays (C) 2013-2014 Serhii Lysovenko
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

from __future__ import print_function
import numpy as np
from scipy.optimize import fmin

_SH_FUNCTIONS = {"Gaus": lambda the_x, x0, h, w:
                 h * np.exp(-(the_x - x0) ** 2 / w),
                 "Lorentz": lambda the_x, x0, h, w:
                 h / (1. + (the_x - x0) ** 2 / w),
                 "P-Voit": lambda the_x, x0, h, w:
                 h / (1. + (the_x - x0) ** 2 / w) ** 2}


def calc_bg(sig_x, sig_y, deg, bf=3.):
    tbg = np.polyval(np.polyfit(sig_x, sig_y, deg), sig_x)
    sigma2 = ((sig_y - tbg) ** 2).sum() / (len(tbg) - 1. - deg)
    sigma2p = None
    while sigma2p != sigma2:
        sigma2p = sigma2
        sigma = sigma2 ** .5 * bf
        pts = zip(sig_x, sig_y, tbg)
        pts = [(a, b) for a, b, c in pts if b - c < sigma]
        pts = np.array(pts).transpose()
        coeffs = np.polyfit(pts[0], pts[1], deg)
        pbg = np.poly1d(coeffs)
        sigma2 = ((pts[1] - pbg(pts[0])) ** 2).sum() / (len(pts[0]) - 1. - deg)
        tbg = pbg(sig_x)
    return tbg, sigma2, coeffs


def refl_sects(s_x, s_y, sbg, sigma2, bf=3.):
    sigma = sigma2 ** .5 * bf
    sector = []
    prev = []
    for x, y in zip(s_x, s_y - sbg):
        if y > sigma:
            if prev:
                sector = prev
                prev = []
            sector.append((x, y))
        elif sector:
            sector.append((x, y))
            if y < 0.:
                yield sector
                sector = []
                prev.append((x, y))
        elif prev and prev[-1][1] - y > y or y <= 0.:
            prev = [(x, y)]
        else:
            prev.append((x, y))
    if sector:
        yield sector


class ReflexDedect:
    """treat sector of points positioned above background"""
    def __init__(self, sector, lambda21=None, I2=.5):
        tps = np.array(sector).transpose()
        self.x_ar = tps[0]
        self.y_ar = tps[1]
        if self.y_ar[0] < 0.:
            x1, x2 = self.x_ar[:2]
            y1, y2 = self.y_ar[:2]
            self.y_ar[0] = 0.
            self.x_ar[0] = x1 - y1 * (x2 - x1) / (y2 - y1)
        if self.y_ar[-1] < 0.:
            x1, x2 = self.x_ar[-2:]
            y1, y2 = self.y_ar[-2:]
            self.y_ar[-1] = 0.
            self.x_ar[-1] = x1 - y1 * (x2 - x1) / (y2 - y1)
        self.peaks = None
        self.lambda21 = lambda21
        self.I2 = I2
        self.sigma2 = (tps[1] ** 2).sum() / len(tps[0])
        self.y_max2 = tps[1].max() ** 2

    def calc_deviat(self, x, fixx=False, fixs=None):
        if fixx:
            the_x = np.zeros((len(x) / 2, 3))
            the_x[:, 0] = self.x0
            the_x[:, 1:3] = x.reshape(len(x) / 2, 2)
            x = the_x.reshape(len(the_x) * 3)
        elif fixs:
            the_x = np.zeros((len(self.x0), 3))
            nfl = len(self.x0) - len(fixs)
            x0 = x[:nfl].tolist()
            for i in fixs:
                x0.insert(i, self.x0[i])
            the_x[:, 0] = x0
            the_x[:, 1:3] = x[nfl:].reshape(len(self.x0), 2)
            x = the_x.reshape(len(the_x) * 3)
        the_x = self.x_ar
        tpx = x.reshape(len(x) / 3, 3).transpose()
        if x.min() <= 0.:
            return np.inf
        shape = self.calc_shape(x)
        dev = self.y_ar - shape
        return (dev ** 2).sum() / (len(the_x))

    def calc_deviat2(self, x):
        the_x = np.array([self.x0, self.h] + x.tolist())
        shape = self.calc_shape(the_x)
        return ((self.dy_ar - shape) ** 2).sum() / len(self.dy_ar)

    def calc_deviat3(self, x):
        the_x = np.zeros(((len(x) - 1) // 2, 3))
        the_x[:, :2] = x[: -1].reshape(len(the_x), 2)
        if the_x[:, 1].min() <= 0. or the_x[:, 1].max() > self.max_h:
            return np.inf
        mulout = the_x[:, 0].min() < self.x_ar[0] or \
            the_x[:, 0].max() > self.x_ar[-1]
        the_x[:, 2] = x[-1]
        the_x = the_x.reshape(len(the_x) * 3)
        shape = self.calc_shape(the_x)
        dev = self.y_ar - shape
        rv = (dev ** 2).sum() / len(self.y_ar)
        if mulout:
            return rv * 100000.0
        return rv

    def calc_shape(self, x=None):
        the_x = self.x_ar
        shape = np.zeros(len(the_x))
        l21 = self.lambda21
        I2 = self.I2
        sh_func = self.sh_func
        if x is None:
            peaks = self.peaks
            if peaks is None:
                return shape
        else:
            peaks = x.reshape(len(x) / 3, 3)
        if l21 is None:
            for x0, h, w in peaks:
                shape += sh_func(the_x, x0, h, w)
        else:
            for x0, h, w in peaks:
                shape += sh_func(the_x, x0, h, w)
                shape += sh_func(the_x, x0 * l21, h * I2, w * l21 ** 2)
                # TODO: enshure if this is correct
        return shape

    def find_bells(self, sigmin, varsig, max_peaks=None, sh_type="Gaus"):
        "my new not so good algorithm"
        self.sh_type = sh_type
        self.sh_func = _SH_FUNCTIONS[sh_type]
        wmin = 2. * sigmin ** 2
        y_ar = self.y_ar
        x_ar = self.x_ar
        area = np.trapz(y_ar, x_ar)
        hght = y_ar.max()
        if self.lambda21:
            area /= 1. + self.I2
            hght /= 1. + self.I2
        self.max_h = hght
        mp = (len(x_ar)) // 4
        if max_peaks is None or max_peaks <= 0 or max_peaks > mp:
            max_peaks = mp
        sigma2 = (y_ar ** 2).sum() / len(y_ar)
        self.peaks = None
        proc_search = True
        done = 0
        peak_add = True
        opt_x = np.array([])
        while True:
            prev_opt_x = opt_x
            prev_sigma2 = sigma2
            done += 1
            xh = np.zeros(done * 2)
            h = hght / done
            w = ((area / done) / h) ** 2 / np.pi
            xh = xh.reshape(done, 2)
            xh[:, 0] = np.linspace(x_ar[0], x_ar[-1], done + 2)[1: -1]
            xh[:, 1] = h
            opt_x = np.zeros(done * 2 + 1)
            opt_x[:-1] = xh.reshape(done * 2)
            opt_x[-1] = w
            opt_x, sig2, itr, fcs, wflg = \
                fmin(self.calc_deviat3, opt_x, full_output=True, disp=False)
            if prev_sigma2 < sigma2:
                if done > 1:
                    opt_x = prev_opt_x
                    done -= 1
                break
            if done == max_peaks:
                break
        bls = np.zeros((done, 3))
        bls[:, :2] = opt_x[:-1].reshape(done, 2)
        bls[:, 2] = opt_x[-1]
        bls = bls.reshape(done * 3)
        if varsig:
            bls, sig2 = fmin(self.calc_deviat, bls,
                             full_output=True, disp=False)[:2]
        bft = [i for i in bls.reshape(done, 3) if i[2] > wmin]
        if len(bft) < done:
            done = len(bft)
            bls = np.array(bft).reshape(done * 3)
            if done > 0:
                bls, sig2 = fmin(self.calc_deviat, bls,
                                 full_output=True, disp=False)[:2]
        self.peaks = zip(*bls.reshape(done, 3).transpose())
        return self.peaks, np.sqrt(sig2)

    def find_bells_pp(self, sh_type, poss, fposs):
        self.peaks = None
        nbells = len(poss)
        self.sh_type = sh_type
        self.sh_func = _SH_FUNCTIONS[sh_type]
        if nbells == 0:
            return [], 0.
        y_ar = self.y_ar
        x_ar = self.x_ar
        area = np.trapz(y_ar, x_ar)
        hght = y_ar.max()
        if self.lambda21:
            area /= 1. + self.I2
            hght /= 1. + self.I2
        h = hght / nbells
        w = ((area / nbells) / h) ** 2 / np.pi
        opt_x = np.zeros((nbells, 2))
        opt_x[:, 0] = h
        opt_x[:, 1] = w
        self.x0 = np.array(poss)
        opt_x = opt_x.reshape(nbells * 2)
        opt_x, sig2 = fmin(self.calc_deviat, opt_x, args=(True,),
                           full_output=True, disp=False)[:2]
        fx = np.zeros((nbells, 3))
        if fposs:
            flx = [self.x0[i] for i in range(len(self.x0)) if i not in fposs]
            opt_x = np.array(flx + opt_x.tolist())
            opt_x, sig2 = fmin(self.calc_deviat, opt_x, args=(False, fposs),
                               full_output=True, disp=False)[:2]
            nfx = len(self.x0) - len(fposs)
            x0 = opt_x[:nfx].tolist()
            for i in fposs:
                x0.insert(i, self.x0[i])
            fx[:, 0] = x0
            fx[:, 1:] = opt_x[nfx:].reshape(nbells, 2)
            opt_x = fx.reshape(nbells * 3)
        else:
            fx[:, 0] = self.x0
            fx[:, 1:] = opt_x.reshape(nbells, 2)
            opt_x = fx.reshape(nbells * 3)
            opt_x, sig2 = fmin(self.calc_deviat, opt_x, full_output=True,
                               disp=False)[:2]
        self.peaks = zip(*opt_x.reshape(nbells, 3).transpose())
        return self.peaks, np.sqrt(sig2)

    def find_peaks(self, bg_sigma2, max_peaks=None):
        "fit by multiple gausians"
        y_ar = self.y_ar
        x_ar = self.x_ar
        mp = (len(x_ar)) // 4
        if max_peaks is None or max_peaks <= 0 or max_peaks > mp:
            max_peaks = mp
        # No reducing
        self.red_allow = 0
        # TODO: Improve algorithm
        sigma2 = (y_ar ** 2).sum() / len(y_ar)
        opt_x = np.array([])
        self.peaks = None
        proc_search = True
        done = 0
        peak_add = True
        while proc_search:
            prev_opt_x = opt_x
            prev_sigma2 = sigma2
            dy_ar = y_ar - self.calc_shape(opt_x)
            maxpt = x_ar[dy_ar.argmax()]
            self.x0 = maxpt
            self.dy_ar = dy_ar
            wdth = (x_ar[-1] - x_ar[0]) ** 2 / 16.
            if self.lambda21:
                self.h = dy_ar.max() / 1.5
            else:
                self.h = dy_ar.max()
            if peak_add:
                hw = fmin(self.calc_deviat2, np.array([wdth]), disp=False)
                opt_x = np.array(list(opt_x) + [maxpt, self.h] + hw.tolist())
            else:
                peak_add = True
            opt_x, sigma2, itr, fcs, wflg = \
                fmin(self.calc_deviat, opt_x, full_output=True, disp=False)
            done += 1
            tpx = opt_x.reshape(len(opt_x) / 3, 3).transpose()
            if sigma2 >= prev_sigma2 or \
                    opt_x.min() <= 0.:
                print('Warning: on fail')
                opt_x = prev_opt_x
                break
            if done >= max_peaks:
                print('Warning: on max')
                break
            if sigma2 <= bg_sigma2:
                opt_x, reduced, sgm = self.reduce_x(opt_x)
                if reduced:
                    peak_add = False
                    sigma2 = sgm
                else:
                    break
        self.peaks = zip(*opt_x.reshape(len(opt_x) / 3, 3).transpose())
        if len(self.peaks) == 0:
            print(x_ar)
            print(y_ar)
        return self.peaks

    def reduce_x(self, x):
        if len(x) < 6 or not self.red_allow:
            return x, False, None
        pcs = len(x) / 3
        oxm = x.reshape(pcs, 3)
        reduced = False
        sigma2 = None
        if oxm[:, 2].mean() * 6 < oxm[:, 2].max():
            reduced = True
            self.red_allow -= 1
            pm = oxm[:, 2].argmax()
            x0, h, w = oxm[pm]
            oxm[pm:-1] = oxm[pm + 1:]
            pcs -= 1
            oxm = np.resize(oxm, (pcs, 3))
            oxm[:, 1] += self.sh_func(oxm[:, 0], x0, h, w)
            x = oxm.reshape(pcs * 3)
            self.x0 = oxm[:, 0]
            tox = oxm[:, 1:].reshape(pcs * 2)
            tox, sigma2, itr, fcs, wflg = fmin(
                self.calc_deviat, tox, args=(True,), full_output=True,
                disp=False)
            x = np.zeros((pcs, 3))
            x[:, 0] = self.x0
            x[:, 1:] = tox.reshape(pcs, 2)
            x = x.reshape(pcs * 3)
        return x, reduced, sigma2
