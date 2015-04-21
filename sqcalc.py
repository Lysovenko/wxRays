#!/usr/bin/env python
# -*- coding: utf-8 -*-
"sqcalc.py"
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

import f2inec as f2i
import numpy as np
from scipy.optimize import fmin, leastsq, fmin_bfgs
from math import ceil
from warnings import simplefilter
# from scipy.interpolate import UnivariateSpline


def norm_pcompt(exi, exq, sqd):
    lmnts = sqd["Elements"]
    f2id = f2i.get_f2i_dict()
    F2 = f2i.f2_calc(f2id, exq, lmnts)
    I_ic = f2i.inec_calc(f2id, exq, lmnts)
    Knorm = np.trapz((F2 + I_ic) * exq ** 2, exq) / \
        np.trapz(exi * exq ** 2, exq)
    sqd["F^2 n"] = F2 / Knorm
    sqd["background"] = (I_ic + F2) / Knorm
    return (Knorm * exi - I_ic) / F2 - 1.


# ## Stetsiv evaluators ###
def stev_pcf(pol_ar, nexi, exq, exq2, pic, icar, bma, inexi):
    d_0 = (inexi - np.sum(pol_ar * icar)) / bma
    nsbg = np.polyval(list(pol_ar) + [d_0], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    csq = (nexi - nsbg) / k_med
    return (pic + np.trapz(csq * exq2, exq)) ** 2


def stev_pcfi(pol_ar, nexi, exq, imat, add, dr, icar, bma, inexi):
    d_0 = (inexi - np.sum(pol_ar * icar)) / bma
    nsbg = np.polyval(list(pol_ar) + [d_0], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    csq = (nexi - nsbg) / k_med
    grs = np.trapz(imat * csq, exq) + add + 1.
    return np.trapz(grs ** 2, dx=dr)


def stev_pcfir(opt_ar, nexi, exq, rho0, imat, add, dr, icar, bma, inexi):
    if rho0:
        rho = rho0
    else:
        rho = opt_ar[-1]
        opt_ar = opt_ar[:-1]
    d_0 = (inexi - np.sum(opt_ar * icar)) / bma
    nsbg = np.polyval(list(opt_ar) + [d_0], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    csq = (nexi - nsbg) / k_med
    grs = (np.trapz(imat * csq, exq) + add) / rho + 1.
    return np.trapz(grs ** 2, dx=dr)


def stev_pblk(pol_ar, nexi, exq, icar, bma, inexi, add, rho0, rqmat, r2, dr):
    "Stetsiv evaluator parabolic"
    d_0 = (inexi - np.sum(pol_ar * icar)) / bma
    nsbg = np.polyval(list(pol_ar) + [d_0], exq)
    uis = add * nsbg[0] + np.trapz(rqmat * (nexi - nsbg), exq)
    k_n = -2. / 3. * np.pi ** 2 * ((len(r2) - 1) * dr) ** 3 * rho0 / \
        np.trapz(uis, dx=dr)
    return np.trapz((uis * k_n / r2 + 1.) ** 2, dx=dr)


# ## Stetsif normalized "background" calculators ###
def Stetsiv_mix_nbackground(nexi, exq, n_pol, sqd, clb):
    r"""
    Parabolic + pcfi mix.
    """
    nsbg1, k_norm1 = Stetsiv_pblk_nbackground(nexi, exq, n_pol, sqd, clb)
    bgc1 = np.array(sqd["BG coefs"])
    nsbg2, k_norm2 = Stetsiv_pcfi_nbackground(nexi, exq, n_pol, sqd, clb)
    bgc2 = np.array(sqd["BG coefs"])
    k_norm = k_norm1 + k_norm2
    bgc = (bgc1 * k_norm1 + bgc2 * k_norm2) / k_norm
    sqd["BG coefs"] = bgc.tolist()
    nsbg = (nsbg1 * k_norm1 + nsbg2 * k_norm2) / k_norm
    return nsbg, k_norm / 2.


def Stetsiv_pcf_nbackground(nexi, exq, n_pol, sqd, clb):
    r"""
    Stetsiv background optimizator, using pair correlation function.
    Evaluated function is
    $(2\pi^2\rho_0 + \int_0^{\infty}s(q)q^2 dq)^2$
    """
    rho0 = sqd["At. dens."]
    inexi = np.trapz(nexi, exq)
    q_a = exq[0]
    q_b = exq[-1]
    bma = q_b - q_a
    if n_pol <= 0:
        return inexi / (q_b - q_a)
    pic = 2. * np.pi ** 2 * rho0
    exq2 = exq ** 2
    x0 = np.array([])
    icar = np.array([])
    for crg in xrange(1, n_pol + 1):
        x0 = np.array([0.] + x0.tolist())
        icar = np.array([(q_b ** crg - q_a ** crg) / crg] +
                        icar.tolist())
        x0 = fmin(stev_pcf, x0, args=(nexi, exq, exq2, pic, icar, bma, inexi),
                  disp=False)
        # callback:
        if not clb(crg):
            break
    d_0 = (inexi - np.sum(x0 * icar)) / bma
    sqd["BG coefs"] = x0.tolist() + [d_0]
    nsbg = np.polyval(sqd["BG coefs"], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    return nsbg, 1. / k_med


def Stetsiv_pcfi_nbackground(nexi, exq, n_pol, sqd, clb):
    r"""
    Stetsiv background optimizator, using pair correlation function.
    Evaluated function is
    $\int_0^{r_c}g(r)^2 dr$
    """
    rho0 = sqd["At. dens."]
    r_c = sqd["R_c"]
    rst = sqd["R_c samps"]
    inexi = np.trapz(nexi, exq)
    q_a = exq[0]
    q_b = exq[-1]
    bma = q_b - q_a
    if n_pol <= 0:
        return inexi / (q_b - q_a)
    rarr = np.linspace(0., r_c, rst)
    pic = 2. * np.pi ** 2 * rho0
    exq2 = exq ** 2
    rq = rarr[:, np.newaxis] * exq
    imat = (np.sin(rq) / rq) * (exq2 / pic)
    imat[0][:] = (exq2 / pic)
    add = (np.cos(exq[0] * rarr) * exq[0] / rarr ** 2 -
           np.sin(exq[0] * rarr) / rarr ** 3) / pic
    add[0] = - exq[0] ** 3 / 3. / pic
    dr = rarr[1] - rarr[0]
    x0 = np.array([])
    icar = np.array([])
    for crg in xrange(1, n_pol + 1):
        x0 = np.array([0.] + x0.tolist())
        icar = np.array([(q_b ** crg - q_a ** crg) / crg] +
                        icar.tolist())
        x0 = fmin(stev_pcfi, x0, args=(nexi, exq, imat, add, dr, icar,
                                       bma, inexi), disp=False)
        # callback:
        if not clb(crg):
            break
    d_0 = (inexi - np.sum(x0 * icar)) / bma
    sqd["BG coefs"] = list(x0) + [d_0]
    nsbg = np.polyval(sqd["BG coefs"], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    return nsbg, 1. / k_med


def Stetsiv_pcfir_nbackground(nexi, exq, order, sqd, clb):
    r"""
    Stetsiv background optimizator, using pair correlation function.
    Evaluated function is
    $\int_0^{r_c}g(r)^2 dr$
    Also rho0 is optimized.
    """
    rho0 = sqd["At. dens."]
    r_c = sqd["R_c"]
    rst = sqd["R_c samps"]
    rho_order = sqd["dens. opt. start"]
    inexi = np.trapz(nexi, exq)
    q_a = exq[0]
    q_b = exq[-1]
    bma = q_b - q_a
    if order <= 0:
        return inexi / (q_b - q_a)
    rarr = np.linspace(0., r_c, rst)
    pic = 2. * np.pi ** 2
    exq2 = exq ** 2
    rq = rarr[:, np.newaxis] * exq
    imat = (np.sin(rq) / rq) * (exq2 / pic)
    imat[0][:] = (exq2 / pic)
    add = (np.cos(exq[0] * rarr) * exq[0] / rarr ** 2 -
           np.sin(exq[0] * rarr) / rarr ** 3) / pic
    add[0] = - exq[0] ** 3 / 3. / pic
    dr = rarr[1] - rarr[0]
    x0 = np.array([])
    icar = np.array([])
    rho = rho0
    for crg in xrange(1, order + 1):
        x0 = np.array([0.] + x0.tolist())
        icar = np.array([(q_b ** crg - q_a ** crg) / crg] +
                        icar.tolist())
        if crg == rho_order:
            x0 = np.array(x0.tolist() + [rho0])
            rho = None
        x0 = fmin(stev_pcfir, x0, args=(nexi, exq, rho, imat, add, dr, icar,
                                        bma, inexi), disp=False)
        # callback:
        if not clb(crg):
            break
    if crg >= rho_order:
        rho = x0[-1]
        x0 = x0[:-1]
        print("rho_0 = %g" % rho)
        sqd["At. dens."] = rho
    d_0 = (inexi - np.sum(x0 * icar)) / bma
    sqd["BG coefs"] = list(x0) + [d_0]
    nsbg = np.polyval(sqd["BG coefs"], exq)
    k_med = .5 * ((nsbg - nexi).max() + nsbg.min())
    return nsbg, 1. / k_med


def Stetsiv_pblk_nbackground(nexi, exq, n_pol, sqd, clb):
    r"""
    Stetsiv background optimizator, using parabolic...
    Evaluated function is
    $\int_0^{r_c}(\int_{s_1}^{s_2}[I^n(s)-I^n_b(s)] sr\sin(sr)ds)^2 dr$
    ${}^n$ means normalized
    """
    rho0 = sqd["At. dens."]
    r_c = sqd["R_c"]
    rst = sqd["R_c samps"]
    inexi = np.trapz(nexi, exq)
    q_a = exq[0]
    q_b = exq[-1]
    bma = q_b - q_a
    if n_pol <= 0:
        raise ValueError("polinom has too smal range")
    rarr = np.linspace(r_c / rst, r_c, rst)
    r2 = 2. * np.pi ** 2 * rho0 * rarr ** 2
    rq = rarr[:, np.newaxis] * exq
    rqmat = np.sin(rq) * rq
    add = rarr * exq[0]
    add = exq[0] * (np.cos(add) - np.sin(add) / add)
    dr = rarr[1] - rarr[0]
    x0 = np.array([])
    icar = np.array([])
    for crg in xrange(1, n_pol + 1):
        x0 = np.array([0.] + x0.tolist())
        icar = np.array([(q_b ** crg - q_a ** crg) / crg] +
                        icar.tolist())
        x0 = fmin(stev_pblk, x0, args=(nexi, exq, icar, bma, inexi, add, rho0,
                                       rqmat, r2, dr), disp=False)
        # callback:
        if not clb(crg):
            break
    d_0 = (inexi - np.sum(x0 * icar)) / bma
    sqd["BG coefs"] = x0.tolist() + [d_0]
    nsbg = np.polyval(sqd["BG coefs"], exq)
    r0 = r_c
    k_norm = -2. / 3. * np.pi ** 2 * r0 ** 3 * rho0 / \
        np.trapz(np.trapz(rqmat * (nexi - nsbg), exq) + nsbg[0] * add, dx=dr)
    return nsbg, k_norm


def calc_sq_Stetsiv(exq, exi, *args):
    modes = {"mix": Stetsiv_mix_nbackground, "pcf": Stetsiv_pcf_nbackground,
             "pcfi": Stetsiv_pcfi_nbackground,
             "pblk": Stetsiv_pblk_nbackground,
             "pcfir": Stetsiv_pcfir_nbackground}
    sqd = args[0]
    lmnts = sqd["Elements"]
    prng = sqd["Degree of polynomial"]
    mode = sqd["Calculation mode"]
    f2id = f2i.get_f2i_dict()
    F2 = f2i.f2_calc(f2id, exq, lmnts)
    nexi = exi / F2
    nsbg, k_norm = modes[mode](nexi, exq, prng, *args)
    add_curves = [nexi, nsbg]
    SQ = (nexi - nsbg) * k_norm
    sqd["F^2 n"] = F2 / k_norm
    sqd["background"] = nsbg * F2
    return SQ, add_curves, k_norm


def calc_pknorm(exq, npi, bg0, sps, r_c, rho0):
    """Calculate "parabolic" k_norm
    \\[k_{norm} = \\frac{\\tfrac{2}{3} \\pi^2 r_c^3 \\rho_0}
    {\\int_0^{r_c}\\int_0^q I_{norm}\\sin(rq)rq
    \\,\\mathrm{d}q\\,\\mathrm{d}r}\\]
    exq - expetimental q
    npi - normalized exp. intensity
    bg0 - background line
    sps - spaces
    r_c - cutoff radius
    rho0 - atomic density"""
    rarr = np.linspace(r_c / sps, r_c, sps)
    rq = rarr[:, np.newaxis] * exq
    rqmat = np.sin(rq) * rq
    add = rarr * exq[0]
    add = bg0 * exq[0] * (np.cos(add) - np.sin(add) / add)
    dr = rarr[1] - rarr[0]
    k_norm = -2. / 3. * np.pi ** 2 * r_c ** 3 * rho0 / \
        np.trapz(np.trapz(rqmat * npi, exq) + add, dx=dr)
    return k_norm


class gr_calc:
    def __init__(self, q, s, s0):
        self.q = q
        self.sq = s
        self.a = np.diff(s) / np.diff(q)
        self.b = s[:-1] - self.a * q[:-1]
        self.q1 = q[0]
        self.A = (s[0] - s0) / self.q1 ** 2
        self.s0 = s0

    def __call__(self, r):
        if r:
            q1 = self.q1
            s0 = self.s0
            A = self.A
            pre = ((s0 + 3. * A * q1 ** 2) / r ** 2 - 6. * A / r ** 4) \
                * np.sin(q1 * r) + (6. * q1 * A / r ** 3 - q1 / r *
                                    (s0 + A * q1 ** 2)) * np.cos(q1 * r)
            qr = self.q * r
            sqr = np.sin(qr)
            cqr = np.cos(qr)
            hai = self.b * (sqr[1:] - qr[1:] * cqr[1:] - sqr[:-1] +
                            qr[:-1] * cqr[:-1]) + self.a / r *\
                (2. * (qr[1:] * sqr[1:] + cqr[1:] -
                       qr[:-1] * sqr[:-1] - cqr[:-1]) -
                 qr[1:] ** 2 * cqr[1:] + qr[:-1] ** 2 * cqr[:-1])
            hai = hai.sum() / r ** 2
            return (hai + pre) / r
        else:
            return np.trapz(self.sq * self.q ** 2, self.q) \
                + self.q1 ** 3 / 3. * self.s0 \
                + self.A * self.q1 ** 5 / 5.


def tail_dev(x, q, sq, sig2):
    a, b, c, d = x
    if d < 0.:
        return np.inf
    y = a * np.cos(b * q - c) * np.exp(-d * q) / q
    return np.sum(np.square(sq - y) / sig2)


def tail_dev_der(x, q, sq, sig2):
    a, b, c, d = x
    premul = (a * np.cos(b * q - c) * np.exp(-d * q) / q - sq) / sig2
    res = np.zeros_like(x)
    premul *= np.exp(-d * q)
    res += 2. / len(q)
    res[0] *= np.sum(premul * np.cos(b * q - c) / q)
    res[1] *= -np.sum(premul * a * np.sin(b * q - c))
    res[2] *= np.sum(premul * a * np.sin(b * q - c) / q)
    res[3] *= -np.sum(premul * a * np.cos(b * q - c))
    return res


def tail_int(r, a, b, c, d, qe):
    a_ = b + r
    b_ = r - b
    d2 = d ** 2
    qa_ = qe * a_
    qac_ = qa_ - c
    qe_ = qe * b_
    qec_ = qe_ + c
    res = a / 2. * np.exp(-d * qe) * \
        ((a_ * np.cos(qac_) + d * np.sin(qac_)) / (d2 + a_ ** 2) +
         (b_ * np.cos(qec_) + d * np.sin(qec_)) / (d2 + b_ ** 2))
    return res


def tail_xy(coefs, start, end, steps):
    "used to plot tail"
    a, b, c, d = coefs
    x = np.linspace(start, end, steps)
    y = a * np.cos(b * x - c) * np.exp(-d * x) / x
    return x, y


def calc_gr_arr(rarr, q, sq, rho0, sqd, **other):
    s0 = sqd.get("S(0)", -1.)
    tail = sqd.get("tail")
    drop = sqd.get("drop tail", False)
    if tail:
        ad = tail["coefs"]
        tail = tail["points"]
    if drop and tail:
        vgr = np.vectorize(gr_calc(q[:-tail], sq[:-tail], s0))
        qe = q[-tail - 1]
    else:
        vgr = np.vectorize(gr_calc(q, sq, s0))
        qe = q[-1]
    gr = vgr(rarr)
    gr /= rho0 * 2. * np.pi ** 2
    gr += 1.
    if tail:
        if ad[3] < 0.:
            raise ValueError("Bad tail function coef c_4: %g" % ad[3])
        rpr = rho0 * 2. * np.pi ** 2 * rarr
        gr += tail_int(rarr, *ad, qe=qe) / rpr
    return gr


def sq_tail(q, sq, lmn, prevc):
    "calculate s(q) tail"
    f2id = f2i.get_f2i_dict()
    sig2 = 1. / np.square(f2i.f2_calc(f2id, q, lmn))
    coefs = fmin(tail_dev, prevc, args=(q, sq, sig2), xtol=.00001,
                 maxiter=10000, maxfun=50000, disp=False)
    coefs[2] %= 2. * np.pi
    if coefs[3] < 0.:
        raise ValueError("Bad tail function coef c_4: %g" % coefs[3])
    return coefs


def find_first_min(x, y):
    if len(x) != len(y) or len(x) == 0:
        raise IndexError("x and y must have the same size != 0")
    for i in xrange(len(x) - 1, 0, -1):
        if y[i] < 0 and y[i - 1] > y[i]:
            return x[i]
    return x[0]


def calc_rho_rc(exq, pSQ, bg0, grsps, sps, r_c, assum=None):
    """Calculate first approximation of the atomic density and
    make recomendation about cutoff radius"""
    simplefilter("error", np.RankWarning)
    f_kn = lambda j: calc_pknorm(exq, pSQ, bg0, grsps, j, 1.)
    v_kn = np.vectorize(f_kn)
    if assum:
        sh = .05 * r_c
        b = assum - sh
        if b <= 0:
            b = r_c / sps
        e = assum + sh
        if e > r_c:
            e = r_c
        s = int((e - b) / r_c * sps)
        if s < 4:
            s = 4
        x = np.linspace(b, e, s)
    else:
        x = np.linspace(r_c / sps, r_c, sps)
    dx = r_c / sps / 10.
    y = v_kn(x)
    dy = v_kn(x + dx)
    y_ = (dy - y) / dx
    cut = len(y_) - 1
    for i in xrange(len(y_)):
        if y_[i] > 100:
            cut = i
            break
    d_min = 0
    for i in xrange(cut, 0, - 1):
        if y_[i - 1] >= y_[i] and y_[i + 1] > y_[i]:
            d_min = i
            break
    if d_min < 2:
        d_min = 2
    pc = np.polyfit(x[d_min - 2:d_min + 2], y_[d_min - 2:d_min + 2], 2)
    X = - pc[1] / (2. * pc[0])
    sh = (x[1] - x[0])
    for i in range(15):
        sh /= 5.
        x = np.linspace(X - sh, X + sh, 4)
        dx = sh / 30.
        y = v_kn(x)
        dy = v_kn(x + dx)
        y_ = (dy - y) / dx
        try:
            pc = np.polyfit(x, y_, 2)
        except np.RankWarning:
            break
        Xn = - pc[1] / (2. * pc[0])
        if abs(X - Xn) < sh * 5:
            X = Xn
        else:
            break
    return 1. / f_kn(X), X


def esq_calc(exq, csq, lmnts):
    f2id = f2i.get_f2i_dict()
    F2 = f2i.f2_calc(f2id, exq, lmnts)
    kns = []
    for lmn in lmnts:
        kns.append(f2i.f2_calc(f2id, exq, [lmn]) / F2)
    ptls = []
    nels = len(lmnts)
    for i in range(nels):
        ptls.append(kns[i] ** 2)
        for j in range(i + 1, nels):
            ptls.append(kns[i] * kns[j] * 2.)
    sig2 = (1. / F2) ** 2
    return tuple([exq] + [csq] + ptls + [sig2])


def hs_sq_dev(thex, q, sq):
    "calculate S(q) deviation for hard spheres model"
    diam, dens = thex
    etha = 0.5235987755982988 * dens * diam ** 3
    gamma = (1. - etha) ** 4
    alpha = (1. + 2. * etha) ** 2 / gamma / diam ** 3
    beta = - 6. * etha * (1 + .5 * etha) ** 2 / gamma / diam ** 4
    gamma = etha * (1. + 2. * etha) ** 2 / 2. / gamma / diam ** 6
    qd = q * diam
    sind = np.sin(qd)
    cosd = np.cos(qd)
    am = (sind - qd * cosd) / q ** 3
    bm = (2. * (qd * sind + cosd) - qd ** 2 * cosd - 2.) / q ** 4
    gm = (- qd ** 4 * cosd + 4. * (
        qd ** 3 * sind - 3. * (2. * (qd * sind + cosd) - qd ** 2 * cosd)) +
        24.) / q ** 6
    res = 4. * np.pi * diam ** 3 * dens * (alpha * am + beta * bm + gamma * gm)
    hsq = 1. / (1. + res)
    return ((sq - hsq) ** 2).sum()


def hs_sq_1(diam, dens, q):
    "calculate S(q) for hard spheres model (1 particles type)"
    etha = 0.5235987755982988 * dens * diam ** 3
    gamma = (1. - etha) ** 4
    alpha = (1. + 2. * etha) ** 2 / gamma / diam ** 3
    beta = - 6. * etha * (1 + .5 * etha) ** 2 / gamma / diam ** 4
    gamma = etha * (1. + 2. * etha) ** 2 / 2. / gamma / diam ** 6
    qd = q * diam
    sind = np.sin(qd)
    cosd = np.cos(qd)
    am = (sind - qd * cosd) / q ** 3
    bm = (2. * (qd * sind + cosd) - qd ** 2 * cosd - 2.) / q ** 4
    gm = (- qd ** 4 * cosd + 4. *
          (qd ** 3 * sind - 3. * (2. * (qd * sind + cosd) - qd ** 2 * cosd)) +
          24.) / q ** 6
    res = 4. * np.pi * diam ** 3 * dens * (alpha * am + beta * bm + gamma * gm)
    return 1. / (1. + res) - 1.


def calc_hs_head(diam, dens, q, sq):
    return fmin(hs_sq_dev, [diam, dens], (q, sq + 1.),
                disp=False)


def calc_hs_s0(diam, dens, q=None, sq=None):
    if q is not None:
        mp = sq.argmax()
        diam, dens = fmin(hs_sq_dev, [diam, dens],
                          (q[:mp], sq[:mp] + 1.), disp=False)
    etha = np.pi / 6. * dens * diam ** 3
    return (1. - etha) ** 4 / (1. + 2 * etha) ** 2 - 1.


def last_lt_zero(arr):
    lltz = -1
    for i in xrange(len(arr)):
        if arr[i] < 0.:
            lltz = i
    return lltz


def calc_rdf(r, gr, rho):
    return 4. * np.pi * r ** 2 * gr * rho


def max_peak_edges(arr):
    pm = arr.argmax()
    a = pm
    for i in xrange(pm + 1, len(arr)):
        if arr[i] > arr[i - 1]:
            a = i
            break
    if a == pm:
        a = len(arr)
    b = pm
    for i in xrange(pm - 1, -1, -1):
        if arr[i] > arr[i + 1]:
            b = i + 1
            break
    lltz = last_lt_zero(arr) + 1
    if b == pm or b < lltz:
        b = lltz
    return b, a


def max_peak_rdf_area(r, gr, rho):
    b, a = max_peak_edges(gr)
    r = r[b:a]
    rdf = calc_rdf(r, gr[b:a], rho)
    b, a = max_peak_edges(rdf)
    r = r[b:a]
    rdf = rdf[b:a]
    b, a = max_peak_edges(rdf)
    r = r[b:a]
    rdf = rdf[b:a]
    return np.trapz(rdf, r)


def mul_gaus_errf(coefs, x, y):
    sumgaus = np.zeros(len(x))
    for i in xrange(0, len(coefs), 3):
        A, sig, x_0 = coefs[i:i + 3]
        if A < 0. or sig < 0.:
            return np.inf
        sumgaus += A * np.exp(-np.square((x - x_0) / sig))
    return sumgaus - y


def opt_n_gaus(x, y, n):
    x_0 = np.mean(x)
    sig = np.std(x) * 2
    A = np.trapz(y, x) / np.sqrt(np.pi) / n / sig
    tp = (A, sig, x_0)
    coefs = np.empty(n * 3)
    for i in xrange(0, n * 3, 3):
        coefs[i:i + 3] = tp
    result, success = leastsq(
        mul_gaus_errf, coefs, args=(x, y), maxfev=50000 * n)
    for i in xrange(0, n * 3, 3):
        yield tuple(result[i:i + 3])


def max_peak_sym_area(r, gr, rho, n=1):
    b, a = max_peak_edges(gr)
    r = r[b:a]
    rdf = calc_rdf(r, gr[b:a], rho)
    b, a = max_peak_edges(rdf)
    r = r[b:a]
    rdf = rdf[b:a]
    asx = opt_n_gaus(r, rdf, n)
    sasx = [(np.sqrt(np.pi) * np.prod(i[:2]),) + i for i in asx]
    return sasx


def max_peak_asym_area(r, gr, rho):
    b, a = max_peak_edges(gr)
    r = r[b:a]
    rdf = calc_rdf(r, gr[b:a], rho)
    ma = rdf.argmax()
    r = r[:ma]
    rdf = rdf[:ma]
    a, s, x = opt_n_gaus(r, rdf, 1).next()
    return np.sqrt(np.pi) * s * a, a, s, x


class rft_calc:
    def __init__(self, r, gr, rho0):
        self.r = r
        self.gr = gr - 1.
        self.r0 = r[0]
        self.pr4 = 4. * np.pi * rho0

    def __call__(self, q):
        r0 = self.r0
        s0 = (r0 * np.cos(q * r0) - np.sin(q * r0) / q) / q ** 2
        r = self.r
        return self.pr4 * (np.trapz(r / q * self.gr * np.sin(q * r), r) + s0)


def calc_rft_arr(qarr, r, gr, rho0, **other):
    pm = gr.argmax()
    for i in xrange(pm, -1, -1):
        if gr[i] <= 0.:
            break
    if gr[i] <= 0. and len(gr) > i + 1 and gr[i + 1] > 0.:
        x = r[i] - (r[i + 1] - r[i]) / (gr[i + 1] - gr[i]) * gr[i]
        r = r[i:]
        gr = gr[i:]
        gr[0] = 0.
        r[0] = x
    vsq = np.vectorize(rft_calc(r, gr, rho0))
    coefs = other.get("tail")
    if coefs is not None:
        vsq(qarr) + 4. * np.pi * rho0 * tail_int(qarr, *coefs, qe=r[-1])
    return vsq(qarr)


def rft_smooth(exp, rft, exq, lmnts):
    f2id = f2i.get_f2i_dict()
    F2 = f2i.f2_calc(f2id, exq, lmnts)
    sigma2 = 1 / F2 ** 2
    rsigma2 = 1. / sigma2
    sigr = rsigma2.sum() / len(sigma2)
    return (exp / sigma2 + rft * sigr) / (rsigma2 + sigr)


def alt_exp_by_sq(exp, sq, sqd):
    return exp.rev_intens(sq * sqd["F^2 n"] + sqd["background"])


def change_curve(cur, alt, bf):
    "moving experimental points, using changed S(q)"
    sigma = np.sqrt(np.sum(np.square(cur - alt)) / len(cur)) * bf
    for i in xrange(len(cur)):
        if abs(cur[i] - alt[i]) > sigma:
            cur[i] = alt[i]


def gr_tail(r, gr, prevc):
    "calculate g(r) tail"
    coefs = fmin(tail_dev, prevc, args=(r, gr - 1., 1.), xtol=.00001,
                 maxiter=10000, maxfun=50000, disp=False)
    coefs[2] %= 2. * np.pi
    return coefs


def get_from_to(xarr, ffrom, fto):
    ifrom = 0
    ito = len(xarr)
    if ffrom > fto:
        ffrom, fto = fto, ffrom
    for i, v in enumerate(xarr):
        if ffrom > v:
            ifrom = i
        if fto < v:
            ito = i
            break
    return ifrom, ito
