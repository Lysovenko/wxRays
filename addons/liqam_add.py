#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is some interesting addon for an educational program"
# wxRays (C) 2013-2014 Serhii Lysovenko
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


from __future__ import print_function
import wx
import locale as loc
import numpy as np
import sqcalc as sqc
import f2inec as f2i
from core.wx.dialogs import DlgProgressCallb, atof, ValidFloat, v_input
from formtext import poly1d2wiki
import wx.lib.rcsizer as rcs
from core.interface import run_dialog, Value
import os.path as osp
from sys import modules
_DEFAULTS = {"sqcalc_mode": 0, "sqcalc_polrang": 1,
             "sqcalc_optsects": 0, "sqcalc_polrangrho": 1,
             "sqcalc_rc": 1., "sqcalc_rc_num": 10, "eic_bf": 2.,
             "grc_start": 0., "grc_end": 5., "gr_tail_pts": 100,
             "grc_stsrang": 100, "rhorccalc_crude": 5,
             "rft_start": 1., "rft_end": 20., "rft_steps": 1000,
             "rhorccalc_accur": 3, "rhorccalc_prang": 5,
             "rhorccalc_cutoff": 4., "rhorccalc_parsamp": 100,
             "rhorccalc_searsamp": 100, "grc_1st_max": 0}

PN_RDF = _("Radial distribution function")
PN_SSF = _("Structure factor")
PN_AIC = _("Alternative intensity curve")
PN_RFT = _("Reverse Fourier transform")
PN_ADE = _("At. dens. evol.")
PN_RDFT = _("Radial distribution function's tail")
PN_BCKGND = _("Background curve")


def introduce(data):
    id = data["id"]
    d = "data"
    f = "file"
    lm = "LIQAM misc"
    mitems = [(d, {"on init": False, "liq samp": True},
               _("Calculate S(q)..."), Menu_call(data, "calc_sq"), None, id),
              (d, {"on init": False, "liq samp": True},
               _("Calculate atomic density..."),
               Menu_call(data, "calc_rho"), None, id),
              (d, {"on init": False, "sq found": True},
               _("Find SF's head..."),
               Menu_call(data, "sq_head"), None, id),
              (d, {"on init": False, "sq found": True},
               _("Find SF's tail..."),
               Menu_call(data, "sq_tail"), None, id),
              (d, {"on init": False, "sq found": True},
               _("Calculate RDF..."),
               Menu_call(data, "calc_gr"), None, id),
              (d, {"on init": False, "on plot": set([PN_RDF, PN_RDFT])},
               _("Find RDF's tail..."), Menu_call(data, "tail_gr"), None, id),
              (d, {"on init": False, "sq found": False, "sq changed": False,
                   "gr found": True},
               _("Perform RFT..."), Menu_call(data, "rft_calc"), None, id),
              (d, {"on init": False, "sq found": False, "sq changed": False,
                   "RFT made": True},
               _("Smooth S(q) by RFT"),
               Menu_call(data, "sq_rft_smooth"), None, id),
              (d, {"on init": False, "sq changed": True},
               _("Find intensity curve by S(q)"),
               Menu_call(data, "alt_exp"), None, id),
              (d, {"on init": False, "alt I found": True,
                   "exp I changed": False, "sq found": False,
                   "sq changed": False},
               _("Change initial intensity curve..."),
               Menu_call(data, "change_exp"), None, id),
              (f, {"on init": False, "sq found": True},
               _("S&ave S(q) file..."),
               Menu_call(data, "save_sq"), wx.ART_FILE_SAVE, id),
              (d, {"on init": False, "sq found": True}, _("SF modifiers"),
               None, None, id, wx.ITEM_NORMAL, lm),
              (lm, {"on init": False, "sq found": False, "sq changed": False,
                    "SF head found": True, "exp I changed": False},
               _("Fit to head"), Menu_call(data, "head_sf_fit"), None, id),
              (lm, {"on init": False, "sq found": False, "sq changed": False,
                    "SF tail found": True, "exp I changed": False},
               _("Fit to tail"), Menu_call(data, "tail_sf_fit"), None, id)]
    data["menu"].add_item
    for i in mitems:
        data["menu"].add_item(*i)
    APP_SETT.declare_section("LIQAM")
    iget = APP_SETT.get
    for i in _DEFAULTS:
        data[i] = iget(i, _DEFAULTS[i], "LIQAM")


def terminate(data):
    iset = APP_SETT.set
    for i in _DEFAULTS:
        iset(i, data[i], "LIQAM")
    modules.pop("sqcalc")


class Menu_call:
    def __init__(self, data, action):
        self.data = data
        self.__call__ = getattr(self, action)

    def calc_sq(self, evt):
        dat = self.data
        if "Exp. data" in dat["data"]:
            dialog_data = {
                "rename": _("Calculation of the structure factor"),
                "lab_elements": _("Elements:"),
                "calc_mod": _("Calculation mode"),
                "clsc": _("Classic"),
                "mix": _("By Stetsiv (mix)"),
                "pcf": _("By Stetsiv (PCF)"),
                "pcfi": _("By Stetsiv (PCF integrated)"),
                "pcfir": _("By Stetsiv (PCF dens. opt.)"),
                "pblk": _("By Stetsiv (parabolic)"),
                "pol_range": _("Polynomial's range:"),
                "at_dens": _("Atomic density:"),
                "start_dens": _("Start dens. opt.:"),
                "r_cutoff": _("Cutoff radius:"),
                "samples": _("Samples:"),
                "sections": _("Sections:"),
                # values
                "elements_ea": Value(Elements),
                "rho0_ea": Value(float),
                "sqcalc_optcects": Value(int),
                "ord_r_spin": Value(int),
                "r_c": Value(float),
                "rc_num": Value(float),
                "pol_spin": Value(int),
                #
                'sqcalc_mode': 0, 'on_mode_change': None, 'pol_spin': 3,
                'sqcalc_optcects': 3, "ord_r_spin": 3, "rc_num": 5}
            res = run_dialog(dialog_data, osp.join(
                osp.dirname(__file__), "liq_am.xml"), "dialog S(q) calc")
            print(res)
            return
            # Just for test
            dialog = DlgSqCalc(dat)
            if dialog.ShowModal() == wx.ID_OK:
                dat["menu"].action_catch("sq found")
                dialog.calculate_sq(dat["data"], dat["plot"])
            dialog.Destroy()

    def calc_rho(self, evt):
        dat = self.data
        if "Exp. data" in dat["data"]:
            dialog = DlgRhoRcCalc(dat)
            if dialog.ShowModal() == wx.ID_OK:
                dialog.calc_roho_rc(dat["data"], dat["plot"])
            dialog.Destroy()

    def calc_gr(self, evt):
        dat = self.data
        if "SSF" in dat["data"]:
            dlg = DlgGrCalc(dat)
            if dlg.ShowModal() == wx.ID_OK:
                dlg.plot_gr(dat["data"]["SSF"], dat["plot"])
                dlg.get_areas()
            dlg.Destroy()

    def save_sq(self, evt):
        save_sq_file(self.data["window"])

    def sq_picker(self, evt, data, selected):
        if not len(evt.ind):
            return False
        xar, yar = data.plots[0][:2]
        pt = np.square(xar - evt.mouseevent.xdata).argmin()
        selected.set_data(xar[pt], yar[pt])
        selected.set_visible(True)
        self.data["SQ point"] = int(pt)
        return True

    def sq_tail(self, evt):
        dat = self.data
        if "SSF" not in dat["data"]:
            return
        q, sq, sqd = dat["data"]["SSF"][:3]
        if "SQ point" in dat:
            tail = len(q) - dat["SQ point"]
        else:
            tail = sqd.get("tail", {"points": 4})["points"]
        if tail < 4:
            tail = 4
        a, b, c, d = sqd.get("tail", {"coefs": [1., 2., 1., .1]})["coefs"]
        if d < .1:
            d = .1
        tail = _("Points:"), tail, 4, len(q)
        a = "a:", float(a)
        b = "b:", float(b)
        c = "c:", float(c)
        d = "d:", float(d)
        rv = v_input(dat["window"], _("Tail init params"), tail, a, b, c, d)
        if rv is None:
            return
        tail, a, b, c, d = rv
        lmn = sqd["Elements"]
        prevc = a, b, c, d
        coefs = sqc.sq_tail(q[-tail:], sq[-tail:], lmn, prevc)
        sqd["tail"] = {"coefs": coefs, "points": tail}
        plot_sq(dat, q, sq, sqd)
        dat["menu"].action_catch("SF tail found")

    def sq_head(self, evt):
        dat = self.data
        if "SSF" not in dat["data"]:
            return
        q, sq, sqd = dat["data"]["SSF"][:3]
        if "SQ point" not in dat:
            head = int(sq.argmax() + 1)
        else:
            head = dat["SQ point"] + 1
        diam = 2.
        dens = float(dat["data"]["Exp. data"].rho0)
        rv = v_input(dat["window"], _("Head init. params"),
                     (_("Points:"), head, 3, len(q)),
                     (_("Diam:"), diam), (_("Dens:"), dens))
        if rv is None:
            return
        head, diam, dens = rv
        diam, dens = sqc.calc_hs_head(diam, dens, q[:head], sq[:head])
        sqd["head"] = {"diam": diam, "dens": dens, "points": head,
                       "S(0)": sqc.calc_hs_s0(diam, dens)}
        plot_sq(dat, q, sq, sqd)
        dat["menu"].action_catch("SF head found")

    def sq_rft_smooth(self, evt):
        dat = self.data
        sq = dat["data"].get("SSF")
        sqd = sq[2]
        rft_sq = dat["data"].pop("RFT sq", None)
        if sq is None or rft_sq is None:
            return
        sqn = sqc.rft_smooth(sq[1], rft_sq, sq[0], sqd["Elements"])
        for i in ("head", "tail"):
            sqd.pop(i, None)
        dat["data"]["SSF"] = (sq[0], sqn, sqd)
        plot_sq(dat, sq[0], sqn, sqd)
        dat["menu"].action_catch("sq changed")

    def alt_exp(self, evt):
        "changes experimental intensity"
        dat = self.data
        sq = dat["data"].get("SSF")
        exp = dat["data"].get("Exp. data")
        if sq is None or exp is None:
            return
        alt_i = sqc.alt_exp_by_sq(exp, sq[1], sq[2])
        pld = dat["plot"].get_data(_("Intensity curve")).clone()
        pld.append((exp.x_data, alt_i, 1))
        pld.journal.log("exp. intens. changed")
        dat["alt I"] = alt_i
        dat["plot"].set_data(PN_AIC, pld).discards.update(
            ("exp I changed", "sq changed", "sq found"))
        dat["menu"].action_catch("alt I found")
        dat["plot"].plot_dataset(PN_AIC)

    def change_exp(self, evt):
        dat = self.data
        alt_i = dat.get("alt I")
        exp = dat["data"].get("Exp. data")
        if exp is None or alt_i is None:
            return
        rv = v_input(dat["window"], _("Believe factor"),
                     (_("The visible part only"), False),
                     (_("Believe factor:"), dat["eic_bf"]))
        if rv is None:
            return
        ov, bf = rv
        dat["eic_bf"] = bf
        if ov:
            if dat["plot"].get_cur_key() != PN_AIC:
                return
            beg, end = dat["plot"].axes1.get_xbound()
            ib, ie = sqc.get_from_to(exp.x_data, beg, end)
            chy = exp.y_data[ib:ie]
            sqc.change_curve(chy, alt_i[ib:ie], bf)
            exp.y_data[ib:ie] = chy
        else:
            sqc.change_curve(exp.y_data, alt_i, bf)
        from core.wx.plot import plot_exp_data
        plot_exp_data(dat["plot"], exp, dat["menu"])
        dat.pop("alt I")
        dat["menu"].action_catch("exp I changed")

    def rft_calc(self, evt):
        "changes experimental intensity"
        dat = self.data
        rdf = dat.get("RDFd")
        if rdf is None:
            return
        strt = _("Start:"), dat["rft_start"]
        end = _("End:"), rdf.get("tail_s", dat["rft_end"])
        rang = _("Steps:"), dat["rft_steps"], 100, 100000
        refur = v_input(dat["window"], _("RFT params"), strt, end, rang)
        if refur is None:
            return
        q = rdf["q"]
        strt, end, rang = refur
        dat["rft_start"], dat["rft_end"], dat["rft_steps"] = strt, end, rang
        rarr = np.linspace(strt, end, rang)
        gr = sqc.calc_gr_arr(rarr, **rdf)
        q2 = np.linspace(q[0], q[-1], len(q) * 10)
        sq2 = sqc.calc_rft_arr(q2, rarr, gr, **rdf)
        dat["data"]["RFT sq"] = sqc.calc_rft_arr(q, rarr, gr, **rdf)
        pld = dat["plot"].set_data(
            PN_RFT, [(q, rdf["sq"], 1, None, "o"), (q2, sq2, 1)],
            r"$q,\,\AA^{-1}$", "s(q)", "A^{-1}")
        pld.discards.update(("liq samp", "sq found", "sq changed"))
        pld.journal.set_parent(dat["plot"].get_data(PN_RDF).journal)
        pld.journal.log("Reverse Fourier Transform")
        dat["menu"].action_catch("RFT made")
        dat["plot"].plot_dataset(PN_RFT)

    def tail_gr(self, evt):
        dat = self.data
        plot = dat["plot"]
        rdf = dat.get("RDFd")
        if rdf is None:
            return
        beg, end = plot.axes1.get_xbound()
        pts = _("Points:"), dat["gr_tail_pts"], 10, 10000
        beg = _("Start:"), float(beg)
        end = _("End:"), float(end)
        a = "a:", 1.
        b = "b:", 2.
        c = "c:", .1
        d = "d:", .1
        rv = v_input(dat["window"], _("RDF tail"), pts, beg, end, a, b, c, d)
        if rv is None:
            return
        pts, beg, end, a, b, c, d = rv
        dat["gr_tail_pts"] = pts
        rarr = np.linspace(beg, end, pts)
        grarr = sqc.calc_gr_arr(rarr, **rdf)
        coefs = sqc.gr_tail(rarr, grarr, (a, b, c, d))
        x, y = sqc.tail_xy(coefs, beg, end, pts)
        y += 1
        rdf["tail"] = coefs
        rdf["tail_s"] = beg
        pdt = plot.set_data(PN_RDFT, [(rarr, grarr, 1), (x, y, 1)],
                            r"$r,\,\AA$", "g(r)", "A")
        pdt.discards.update(("liq samp", "sq found", "sq changed", "gr found"))
        pdt.journal.log("find RDF's tail")
        info = ["\n\n",
                "''g(r) = 1 + a * cos(b * r - c) * exp(-d * r) / r''",
                "\n\n----\n\n{|\n! %s\n! %s\n"] +\
            ["|-\n| %s\n| %%s\n" % (i,) for i in "a b c d".split()] + ["|}"]
        info = u"".join(info) % ((_("parameter"), _("value")) +
                                 tuple([loc.format("%g", i) for i in coefs]))
        pdt.set_info(info)
        plot.plot_dataset(PN_RDFT)

    def tail_sf_fit(self, evt):
        dat = self.data
        if "SSF" not in dat["data"]:
            return
        q, sq, sqd = dat["data"]["SSF"][:3]
        tail = sqd.get("tail")
        if tail is None:
            return
        pts = tail["points"]
        a, b, c, d = tail["coefs"]
        x = q[-pts:]
        sq[-pts:] = a * np.cos(b * x - c) * np.exp(-d * x) / x
        sqd.pop("tail")
        plot_sq(dat, q, sq, sqd)
        dat["menu"].action_catch("sq changed")

    def head_sf_fit(self, evt):
        dat = self.data
        if "SSF" not in dat["data"]:
            return
        q, sq, sqd = dat["data"]["SSF"][:3]
        head = sqd.get("head")
        if head is None:
            return
        diam = head["diam"]
        dens = head["dens"]
        pts = head["points"]
        sq[:pts] = sqc.hs_sq_1(diam, dens, q[:pts])
        sqd.pop("head")
        plot_sq(dat, q, sq, sqd)
        dat["menu"].action_catch("sq changed")


_MOD_NAMES = {"clsc": _("Classic"), "mix": _("By Stetsiv (mix)"),
              "pcf":  _("By Stetsiv (PCF)"),
              "pcfi": _("By Stetsiv (PCF integrated)"),
              "pcfir": _("By Stetsiv (PCF dens. opt.)"),
              "pblk": _("By Stetsiv (parabolic)")}


def plot_sq(dat, q, sq, sqd):
    plot = dat["plot"]
    plts = [(q, sq, 1, None, "o-", 5)]
    log = ["mode: %s" % sqd["Calculation mode"]]
    info = [u"\n\n== ", _("Calculation details"), " ==\n\n"]
    info += ['{|\n|-\n| ', _("Calculation mode"), "\n| ",
             _MOD_NAMES[sqd["Calculation mode"]], "\n"]
    info += [
        "|-\n| ", _("Elements"), '\n| ', '; '.join(
            ["%s %s" % (i, loc.format("%g", j)) for i, j in sqd["Elements"]]),
        '\n']
    if "Degree of polynomial" in sqd:
        info.append("|-\n| %s\n| %d\n" %
                    (_("Degree of polynomial"), sqd["Degree of polynomial"]))
        log.append("pol. deg: %d" % sqd["Degree of polynomial"])
    if "At. dens." in sqd:
        info.append(u"|-\n| \u03c1_{0}\n| %s\n" %
                    loc.format("%g", sqd["At. dens."]))
        log.append("At. dens.: %g" % sqd["At. dens."])
    if "R_c" in sqd:
        info.append("|-\n| R_{0}\n| %s\n" %
                    loc.format("%g", sqd["R_c"]))
        info.append("|-\n| %s\n| %d\n" %
                    (_("R_{0} samples"), sqd["R_c samps"]))
        log.append("R_c: %g" % sqd["R_c"])
        log.append("R_c samps: %d" % sqd["R_c samps"])
    info.append('|}\n')
    if "BG coefs" in sqd:
        info.append(u"%s:\n\n" % _("The background polynomial"))
        wp1d = poly1d2wiki(sqd["BG coefs"])
        info.append("''f(x) = %s''\n\n" % wp1d)
        log.append("Background: %s" % wp1d)
    info = u"".join(info)
    if "head" in sqd:
        head = sqd["head"]
        diam = head["diam"]
        dens = head["dens"]
        s0 = head["S(0)"]
        head = head["points"]
        qe = q[head - 1]
        etha = np.pi / 6. * dens * diam ** 3
        pts = int(qe * head * 5. / (qe - q[0])) + 1
        qh = np.linspace(0., qe, pts)
        sqh = sqc.hs_sq_1(diam, dens, qh)
        sqh[0] = s0
        plts.append((qh, sqh, 1))
        info += u"".join(
            ["\n\n== %s ==\n\n" % _("Head"),
             "{|\n! %s\n! %s\n" % (_("parameter"), _("value"))] +
            ["|-\n| %s\n| %%s\n" % (i,) for i in (
                _("diameter"), _("Effective density"), u"\u03b7", "S(0)")] +
            ["|}\n\n"]) %\
            tuple([loc.format('%g', i) for i in (diam, dens, etha, s0)])
        log.append("head: %s" % head)
    if "tail" in sqd:
        log.append("tail: %s" % sqd["tail"])
        coefs = sqd["tail"]["coefs"]
        tail = sqd["tail"]["points"]
        x, y = sqc.tail_xy(coefs, q[-tail], q[-1], tail * 10)
        plts.append((x, y, 1))
        ar_info = ["\n\n== %s ==\n\n",
                   "''S(q) = a * cos(b * q - c) * exp(-d * q) / q''",
                   "\n\n----\n\n{|\n! %s\n! %s\n"] +\
            ["|-\n| %s\n| %%s\n" % (i,) for i in "a b c d".split()] + ["|}"]
        info += u"".join(ar_info) % (
            (_("Tail"), _("parameter"), _("value")) +
            tuple([loc.format("%g", i) for i in coefs]))
    pdata = plot.set_data(PN_SSF, plts, r"$s,\,\AA^{-1}$", "S(q)", "A^{-1}")
    pdata.set_picker(Menu_call(dat, "sq_picker"))
    pdata.discards.add("liq samp")
    pdata.journal.set_parent(plot.get_data(_("Intensity curve")).journal)
    pdata.journal.log("structure factor: %s" % "; ".join(log))
    if info:
        pdata.set_info(info)
    plot.plot_dataset(PN_SSF)


class Elements:
    def __init__(self, elements=None):
        lmns = []
        pts = []
        if elements is None:
            self.elements = []
            return
        try:
            for lmn in elements.split(';'):
                spl = lmn.split()
                lmns.append(str(spl[0]))
                pts.append(atof(spl[1]))
        except IndexError:
            raise ValueError(_("Syntax error."))
        spts = sum(pts)
        if spts != 1.:
            pts = [i / spts for i in pts]
        f2id = f2i.get_f2i_dict()
        bad = [i for i in lmns if i not in f2id]
        if bad:
            raise ValueError("nonexisting elements: " +
                             ", ".join(bad))
        self.elements = zip(lmns, pts)

    def __str__(self):
        return "; ".join("{0} {1}".format(i, loc.format("%.4g", j * 100))
                         for i, j in self.elements)


class ValidElements(wx.PyValidator):
    "validator for the 'elements' field"
    err_msg = ""

    def Clone(self):
        return ValidElements()

    def Validate(self, win):
        text_ctrl = self.GetWindow()
        text = text_ctrl.GetValue()
        if self.test_text(text):
            text_ctrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.Refresh()
            return True
        wx.MessageBox(_("Elements is invalid!\n") + self.err_msg, _("Error"))
        text_ctrl.SetBackgroundColour("pink")
        text_ctrl.SetFocus()
        text_ctrl.Refresh()
        return False

    def test_text(self, text):
        if len(text) == 0:
            self.err_msg = _("Field in empty.")
            return False
        f2id = f2i.get_f2i_dict()
        for lmn in text.split(';'):
            spl = lmn.split()
            if len(spl) != 2:
                self.err_msg = _("Syntax error.")
                return False
            if not spl[0] in f2id:
                self.err_msg = _("Element %s not found.") % spl[0]
                return False
            try:
                elpart = atof(spl[1])
            except ValueError:
                self.err_msg = _("Wrong type of float.") + "\n(%s)" % spl[1]
                return False
            if 0. >= elpart:
                self.err_msg = _("Part of element must be > 0.")
                return False
        return True

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True


class DlgSqCalc(wx.Dialog):
    "Missing docstring"
    def __init__(self, internal):
        title = _("Calculation of the structure factor")
        parent = internal["window"]
        data = internal["data"]["Exp. data"]
        rho_rc = internal["data"].get("RhoRc")
        self.internal = internal
        self.data = data
        wx.Dialog.__init__(self, parent, -1, title)
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        # Elements
        rcszr = rcs.RowColSizer()
        label = wx.StaticText(self, -1, _("Elements:"))
        rcszr.Add(label, row=0, col=0, border=5, flag=wx.ALL)
        telements = u''
        if data is not None and data.elements:
            for lmn in data.elements:
                telements += u" %s %s;" % (lmn[0], loc.str(lmn[1]))
            telements = telements[1:-1]
        self.elements_ea = wx.TextCtrl(self, value=telements,
                                       validator=ValidElements())
        rcszr.Add(self.elements_ea, row=0, col=1, colspan=3, flag=wx.EXPAND)
        # mode
        modes = [_MOD_NAMES[i]
                 for i in "clsc mix pcf pcfi pcfir pblk".split()]
        self.calc_modes = wx.RadioBox(
            self, -1, _("Calculation mode"), choices=modes, majorDimension=2,
            style=wx.RA_SPECIFY_COLS)
        self.calc_modes.Bind(wx.EVT_RADIOBOX, self.on_mode_change)
        item = internal["sqcalc_mode"]
        if 0 > item or item >= len(modes):
            item = 0
        self.calc_modes.SetSelection(item)
        rcszr.Add(self.calc_modes, row=1, col=0, colspan=4,
                  flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        # #############  Horizontal line  ###########################
        line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
        rcszr.Add(line, row=2, col=0, colspan=4, flag=wx.EXPAND)
        # pol size
        label = wx.StaticText(self, -1, _("Polynomial's range:"))
        rcszr.Add(label, row=3, col=0, border=5, flag=wx.ALL)
        self.pol_spin = wx.SpinCtrl(self, -1)
        self.pol_spin.SetRange(1, 50)
        rang = internal["sqcalc_polrang"]
        if rang < 1 or rang > 50:
            rang = 1
        self.pol_spin.SetValue(rang)
        rcszr.Add(self.pol_spin, row=3, col=1)
        # sects prev opt
        label = wx.StaticText(self, -1, _("Sections:"))
        rcszr.Add(label, row=4, col=0, border=5, flag=wx.ALL)
        self.opt_sects = wx.SpinCtrl(self, -1)
        self.opt_sects.SetRange(0, 10)
        rang = internal["sqcalc_optsects"]
        if rang < 0 or rang > 10:
            rang = 0
        self.opt_sects.SetValue(rang)
        rcszr.Add(self.opt_sects, row=4, col=1)
        label = wx.StaticText(self, -1, _("Start dens. opt.:"))
        rcszr.Add(label, row=4, col=2, border=5, flag=wx.ALL)
        self.ord_r_spin = wx.SpinCtrl(self, -1)
        self.ord_r_spin.SetRange(1, 50)
        rang = internal["sqcalc_polrangrho"]
        if rang < 1 or rang > 50:
            rang = 1
        self.ord_r_spin.SetValue(rang)
        rcszr.Add(self.ord_r_spin, row=4, col=3)
        # \rho_0
        label = wx.StaticText(self, -1, _("Atomic density:"))
        rcszr.Add(label, row=3, col=2, border=5, flag=wx.ALL)
        trho_0 = ''
        if data is not None and data.rho0:
            trho_0 = loc.format(u"%g", data.rho0)
        if rho_rc:
            if trho_0:
                trho_0 = [trho_0, loc.format(u"%g", rho_rc[0])]
            else:
                trho_0 = loc.format(u"%g", rho_rc[0])
        if type(trho_0) == list:
            self.rho0_ea = wx.ComboBox(
                self, value=trho_0[0], choices=trho_0,
                style=wx.CB_DROPDOWN, validator=ValidFloat())
        else:
            self.rho0_ea = wx.TextCtrl(self, value=trho_0,
                                       validator=ValidFloat())
        rcszr.Add(self.rho0_ea, row=3, col=3)
        # r_c / steps
        label = wx.StaticText(self, -1, _("Cutoff radius:"))
        rcszr.Add(label, row=5, col=0, border=5, flag=wx.ALL)
        if rho_rc:
            r_c = rho_rc[1]
        else:
            r_c = internal["sqcalc_rc"]
        r_c = loc.format("%g", r_c)
        self.rc_ea = wx.TextCtrl(self, value=r_c,
                                 validator=ValidFloat())
        rcszr.Add(self.rc_ea, row=5, col=1)
        label = wx.StaticText(self, -1, _("Samples:"))
        rcszr.Add(label, row=5, col=2, border=5, flag=wx.ALL)
        self.rc_num = wx.SpinCtrl(self, -1)
        self.rc_num.SetRange(3, 1000)
        rang = internal["sqcalc_rc_num"]
        if rang < 3 or rang > 1000:
            rang = 10
        self.rc_num.SetValue(rang)
        rcszr.Add(self.rc_num, row=5, col=3)
        # Buttons...
        btn = wx.Button(self, wx.ID_CANCEL)
        rcszr.Add(btn, row=7, col=0, border=5, flag=wx.ALL)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        rcszr.Add(btn, row=7, col=2, colspan=2,
                  flag=wx.ALIGN_RIGHT | wx.ALL, border=5)
        rcszr.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
                  row=6, col=0, colspan=4, flag=wx.EXPAND)
        rcszr.RecalcSizes()
        self.SetSizer(rcszr)
        rcszr.Fit(self)
        enables = ["000000", "110110", "110000", "110110", "110111", "110110"]
        self.enables = [tuple(map(bool, map(int, i))) for i in enables]
        self.on_mode_change()

    def get_elements(self):
        lmns = []
        pts = []
        for lmn in self.elements_ea.GetValue().split(';'):
            spl = lmn.split()
            lmns.append(str(spl[0]))
            pts.append(atof(spl[1]))
        spts = sum(pts)
        if spts != 1.:
            pts = [i / spts for i in pts]
        return zip(lmns, pts)

    def on_mode_change(self, evt=None):
        sel = self.calc_modes.GetSelection()
        psp, rho0, op_s, rc_n, rc_e, pspr = self.enables[sel]
#        map(bool, self.enables[sel])
        self.pol_spin.Enable(psp)
        self.rho0_ea.Enable(rho0)
        self.opt_sects.Enable(op_s)
        self.rc_num.Enable(rc_n)
        self.rc_ea.Enable(rc_e)
        self.ord_r_spin.Enable(pspr)

    def save_state(self):
        i = self.internal
        i["sqcalc_mode"] = int(self.calc_modes.GetSelection())
        i["sqcalc_polrang"] = int(self.pol_spin.GetValue())
        i["sqcalc_polrangrho"] = int(self.ord_r_spin.GetValue())
        i["sqcalc_optsects"] = int(self.opt_sects.GetValue())
        try:
            i["sqcalc_rc"] = atof(self.rc_ea.GetValue())
        except ValueError:
            pass
        i["sqcalc_rc_num"] = int(self.rc_num.GetValue())

    def calculate_sq(self, gdata, plot):
        self.save_state()
        els = self.get_elements()
        sqd = {"Elements": els}
        # only flat \theta-\theta diffractometer is implementet yet
        exi = self.data.corr_intens()
        exq = self.data.get_qrange()
        add_curves = None
        cmode = self.calc_modes.GetSelection()
        psp, rho0, op_s, rc_n, rc_e, pspr = self.enables[cmode]
        if psp:
            dg_pol = self.pol_spin.GetValue()
            sqd["Degree of polynomial"] = dg_pol
        if rho0:
            sqd["At. dens."] = atof(self.rho0_ea.GetValue())
        if op_s:
            sqd["Sectors"] = self.opt_sects.GetValue()
        if rc_n:
            sqd["R_c samps"] = self.rc_num.GetValue()
        if rc_e:
            sqd["R_c"] = atof(self.rc_ea.GetValue())
        if pspr:
            sqd["dens. opt. start"] = self.ord_r_spin.GetValue()
        cmods = "clsc mix pcf pcfi pcfir pblk"
        sqd["Calculation mode"] = cmods.split()[cmode]
        if cmode == 0:
            rsq = sqc.norm_pcompt(exi, exq, sqd)
        elif 0 < cmode < 6:
            args = (sqd,)
            if cmode == 1:
                dg_pol *= 2
            titl = _("S(Q) by Stetsiv")
            msg = _("Calculating the structure factor "
                    "by the Stetsiv method (%s)...") % sqd["Calculation mode"]
            args += (DlgProgressCallb(self.Parent, titl, msg, dg_pol,
                                      can_abort=True, cumulative=True),)
            rsq, add_curves = sqc.calc_sq_Stetsiv(exq, exi, *args)[:2]
        gdata["SSF"] = (exq, rsq, sqd)
        plot_sq(self.internal, exq, rsq, sqd)
        if add_curves:
            plts = []
            for crv in add_curves:
                plts.append((exq, crv, 1))
            pdata = plot.set_data(PN_BCKGND, plts, r'$s,\, \AA^{-1}$',
                                  r'$I(q)/F^2(q)$', 'A^{-1}')
            pdata.discards.add("liq samp")
            info = ["|-\n| %s\n| *\n| x^{%d}\n" % (loc.format("%g", j), i)
                    for i, j in enumerate(reversed(sqd["BG coefs"]))]
            info = u"".join(["{|\n"] + info + ["|}\n"])
            pdata.set_info(info)
        else:
            plot.pop(PN_BCKGND)


class DlgGrCalc(wx.Dialog):
    "Missing docstring"
    def __init__(self, internal):
        parent = internal["window"]
        data = internal["data"]["Exp. data"]
        sqd = internal["data"]["SSF"][-1]
        title = _("Calculation of the RDF")
        wx.Dialog.__init__(self, parent, -1, title)
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        self.internal = internal
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "S(0):")
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        if "head" in sqd:
            s0 = sqd["head"]["S(0)"]
        else:
            s0 = -1.
        self.s_0 = wx.TextCtrl(self, value=loc.format(u"%g", s0),
                               validator=ValidFloat(lambda x: -1 > x >= 0.))
        box.Add(self.s_0, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn = wx.Button(self, -1, _("Calculate..."))
        box.Add(btn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn.Bind(wx.EVT_BUTTON, self.calc_s0)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.drop_tail = wx.CheckBox(self, -1, _("Drop tail"))
        self.drop_tail.SetValue(internal.get("drop tail", False))
        self.drop_tail.Enable("tail" in sqd)
        box.Add(self.drop_tail, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # \rho_0
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Atomic density:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        trho_0 = []
        if data.rho0:
            trho_0.append(loc.format(u"%g", data.rho0))
        if "At. dens." in sqd and data.rho0 != sqd["At. dens."]:
            trho_0.append(loc.format(u"%g", sqd["At. dens."]))
        if "head" in sqd:
            trho_0.append(loc.format(u"%g", sqd["head"]["dens"]))
        if not trho_0:
            trho_0.append(u'')
        if len(trho_0) > 1:
            self.rho0_ea = wx.ComboBox(
                self, value=trho_0[0], choices=trho_0,
                style=wx.CB_DROPDOWN, validator=ValidFloat())
        else:
            self.rho0_ea = wx.TextCtrl(self, value=trho_0[0],
                                       validator=ValidFloat())
        box.Add(self.rho0_ea, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # start end step
        label = wx.StaticText(self, -1, _("Start, end, steps:"))
        sizer.Add(label, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        val = internal["grc_start"]
        val = loc.format("%g", val)
        self.start_ea = wx.TextCtrl(self, value=val,
                                    validator=ValidFloat(lambda x: x < 0.))
        box.Add(self.start_ea, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        val = internal["grc_end"]
        val = loc.format("%g", val)
        self.end_ea = wx.TextCtrl(self, value=val,
                                  validator=ValidFloat(lambda x: x < 0.))
        box.Add(self.end_ea, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.steps_spin = wx.SpinCtrl(self, -1)
        self.steps_spin.SetRange(10, 1000)
        rang = internal["grc_stsrang"]
        if rang < 10 or rang > 1000:
            rang = 10
        self.steps_spin.SetValue(rang)
        box.Add(self.steps_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # optionals
        self.c_1st_max = wx.CheckBox(self, -1, _("Calculate first maximum"))
        self.c_1st_max.SetValue(internal["grc_1st_max"])
        self.c_1st_max.Bind(wx.EVT_CHECKBOX, self.on_ch_c_1st_max)
        sizer.Add(self.c_1st_max, 0,
                  wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Asym bells: "))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.bells = wx.SpinCtrl(self, min=1, max=5)
        self.bells.SetValue(internal.get("bells", 1))
        self.bells.Enable(internal["grc_1st_max"])
        box.Add(self.bells, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Buttons...
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.fcn = _("First coord")

    def on_ch_c_1st_max(self, evt):
        self.bells.Enable(self.c_1st_max.GetValue())

    def get_rho0(self):
        rho = atof(self.rho0_ea.GetValue())
        self.rho0 = rho
        return rho

    def get_ses(self):
        strt = atof(self.start_ea.GetValue())
        end = atof(self.end_ea.GetValue())
        steps = int(self.steps_spin.GetValue())
        if strt > end:
            strt, end = end, strt
        if strt == end:
            end += 1.
        i = self.internal
        i["grc_stsrang"] = steps
        i["grc_start"] = strt
        i["grc_end"] = end
        return strt, end, steps

    def get_gr(self, q, sq):
        intd = self.internal
        sqd = intd["data"]["SSF"][2]
        s0 = atof(self.s_0.GetValue())
        drop_tail = self.drop_tail.GetValue()
        grd = dict(sqd)
        grd["S(0)"] = s0
        grd["drop tail"] = drop_tail
        intd["drop tail"] = drop_tail
        rarr = np.linspace(*self.get_ses())
        rho = self.get_rho0()
        intd["RDFd"] = {"rho0": rho, "sqd": grd, "q": q, "sq": sq}
        return rarr, sqc.calc_gr_arr(rarr, **intd["RDFd"])

    def get_areas(self):
        ial = self.internal
        ial["grc_1st_max"] = int(self.c_1st_max.GetValue())
        if not ial["grc_1st_max"]:
            return
        r, gr = ial["plot"].get_data(PN_RDF).plots[0][:2]
        rho = self.rho0
        bells = self.bells.GetValue()
        ial['bells'] = bells
        syms = sqc.max_peak_sym_area(r, gr, rho, bells)
        asym = sqc.max_peak_asym_area(r, gr, rho)
        comm = sqc.max_peak_rdf_area(r, gr, rho)
        gaz = 4. * np.pi * rho * r ** 2
        rdf = gaz * gr
        symp = []
        syms.sort()
        infos = ["{|\n! type\n! area\n! location\n! sigma\n"]
        for sym in syms:
            sym, a, s, x0 = sym
            symp.append(a * np.exp(-(r - x0) ** 2 / s ** 2))
        asym, a, s, x0 = asym
        infos.append("| common\n| %g\n" % comm)
        infos.append("| Asymetric\n| %g\n| %g\n| %g\n" %
                     (asym, x0, np.sqrt(s / 2.)))
        asymp = a * np.exp(-(r - x0) ** 2 / s ** 2)
        plts = [(r, rdf, 1), (r, asymp, 1), (r, gaz, 1, "black", "--")] + \
            [(r, i, 1) for i in symp]
        if len(syms) > 1:
            plts.append((r, sum(symp), 1, "gray", "--"))
        dat = ial["plot"].set_data(self.fcn, plts, r"$r,\,\AA$",
                                   r"$\rho(r),\,\AA^{-3}$", "A")
        dat.discards.update(("liq samp", "sq found", "sq changed"))
        if len(syms) > 1:
            infos += ["| Symetric(%d)\n| %g\n| %g\n| %g\n" %
                      (i[0], i[1][0], i[1][3], np.sqrt(i[1][2] / 2.))
                      for i in enumerate(syms, 1)]
            infos.append("| Symetric\n| %g\n" % sum([j[0] for j in syms]))
        else:
            infos.append("| Symetric\n| %g\n| %g\n| %g\n" %
                         (syms[0][0], syms[0][3], np.sqrt(syms[0][2] / 2.)))
        dat.set_info(u"|-\n".join(infos) + "|}\n")
        dat.journal.log("get_areas")

    def plot_gr(self, dsq, plot):
        try:
            rgr = self.get_gr(*dsq[:2])
            pld = plot.set_data(
                PN_RDF, [rgr + (1,)], r"$r,\,\AA$", "g(r)",
                "A")
        except ValueError, err:
            wx.MessageBox(_("Value Error: %s") % err, PROG_NAME, wx.ICON_ERROR)
            return
        pld.discards.update(("liq samp", "sq found", "sq changed"))
        pld.journal.set_parent(plot.get_data(PN_SSF).journal)
        pld.journal.log("calculate RDF")
        q, sq = dsq[:2]
        rho = self.get_rho0()
        self.internal["menu"].action_catch("gr found")
        plot.plot_dataset(PN_RDF)

    def calc_s0(self, evt):
        if not self.Validate():
            return
        internal = self.internal
        diam = internal.get("diam", 2.)
        rv = v_input(self, _("Diameter"), (_("Diam:"), diam))
        if rv is None:
            return
        diam = rv[0]
        dens = self.get_rho0()
        s0 = sqc.calc_hs_s0(diam, dens, *internal['data']["SSF"][:2])
        self.s_0.SetValue(loc.format(u"%g", s0))


class DlgRhoRcCalc(wx.Dialog):
    "Missing docstring"
    def __init__(self, internal):
        parent = internal["window"]
        data = internal["data"]["Exp. data"]
        self.internal = internal
        self.data = data
        title = _("Calc. of prox. at. dens.")
        wx.Dialog.__init__(self, parent, -1, title)
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        sizer = wx.BoxSizer(wx.VERTICAL)
        # elements
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Elements:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        telements = u''
        if data is not None and data.elements:
            for lmn in data.elements:
                telements += u" %s %s;" % (lmn[0], loc.str(lmn[1]))
            telements = telements[1:-1]
        self.elements_ea = wx.TextCtrl(self, value=telements,
                                       validator=ValidElements())
        box.Add(self.elements_ea, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Times crude
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Times crude:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        c_times = internal["rhorccalc_crude"]
        self.tms_spin = wx.SpinCtrl(self, -1)
        self.tms_spin.SetRange(1, 20)
        if c_times < 1 or c_times > 20:
            c_times = 5
        self.tms_spin.SetValue(c_times)
        box.Add(self.tms_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Times accurate
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Times accurate:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        a_times = internal["rhorccalc_accur"]
        self.tmsa_spin = wx.SpinCtrl(self, -1)
        self.tmsa_spin.SetRange(0, 20)
        if c_times < 0 or c_times > 20:
            a_times = 3
        self.tmsa_spin.SetValue(a_times)
        box.Add(self.tmsa_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Range
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Degree of polynomial:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        p_rang = internal["rhorccalc_prang"]
        self.pr_spin = wx.SpinCtrl(self, -1)
        self.pr_spin.SetRange(1, 20)
        if p_rang < 1 or p_rang > 20:
            p_rang = 5
        self.pr_spin.SetValue(p_rang)
        box.Add(self.pr_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # previous cutoff
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Previous cutoff:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        prev_cut = internal["rhorccalc_cutoff"]
        tcutoff = loc.format(u"%g", prev_cut)
        self.prev_cut_ea = wx.TextCtrl(self, value=tcutoff,
                                       validator=ValidFloat())
        box.Add(self.prev_cut_ea, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # parabolic samples
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Parabolic samples:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        par_samp = internal["rhorccalc_parsamp"]
        self.psamps_spin = wx.SpinCtrl(self, -1)
        self.psamps_spin.SetRange(10, 1000)
        if par_samp < 10 or par_samp > 1000:
            par_samp = 100
        self.psamps_spin.SetValue(par_samp)
        box.Add(self.psamps_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # searching samples
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Searching samples:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sear_samp = internal["rhorccalc_searsamp"]
        self.ssamps_spin = wx.SpinCtrl(self, -1)
        self.ssamps_spin.SetRange(100, 2000)
        if sear_samp < 100 or par_samp > 2000:
            sear_samp = 100
        self.ssamps_spin.SetValue(sear_samp)
        box.Add(self.ssamps_spin, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Buttons...
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def save_state(self):
        inter = self.internal
        inter["rhorccalc_cutoff"] = atof(self.prev_cut_ea.GetValue())
        inter["rhorccalc_parsamp"] = self.psamps_spin.GetValue()
        inter["rhorccalc_searsamp"] = self.ssamps_spin.GetValue()
        inter["rhorccalc_crude"] = self.tms_spin.GetValue()
        inter["rhorccalc_accur"] = self.tmsa_spin.GetValue()
        inter["rhorccalc_prang"] = self.pr_spin.GetValue()

    def get_elements(self):
        for lmn in self.elements_ea.GetValue().split(';'):
            spl = lmn.split()
            yield str(spl[0]), atof(spl[1])

    def calc_roho_rc(self, data, plot=None):
        if self.data is None:
            return
        sqd = {}
        sqd["Elements"] = tuple(self.get_elements())
        exi = self.data.corr_intens()
        exq = self.data.get_qrange()
        c_tms = self.tms_spin.GetValue()
        a_tms = self.tmsa_spin.GetValue()
        p_rng = self.pr_spin.GetValue()
        sqd["Degree of polynomial"] = p_rng
        pars = self.psamps_spin.GetValue()
        sqd["R_c samps"] = pars
        sear = self.ssamps_spin.GetValue()
        prc = atof(self.prev_cut_ea.GetValue())
        clb = DlgProgressCallb(
            self.Parent, _("Calc. of prox. at. dens."),
            _("Calculating proximately atomic density..."),
            (c_tms + a_tms) * (p_rng + 1), can_abort=True, cumulative=True)
        rho_col = []
        rho = 1.
        sqd["Calculation mode"] = "pcfi"
        sqd["R_c"] = prc
        for i in range(c_tms):
            sqd["At. dens."] = rho
            sSQ, crvs, ks = sqc.calc_sq_Stetsiv(exq, exi, sqd, clb)
            if not clb:
                return
            bg0 = crvs[1][0] * ks
            rho, rcc = sqc.calc_rho_rc(exq, sSQ, bg0, pars, sear, prc)
            if not clb(1):
                return
            if plot is not None:
                rho_col.append((rho, rcc))
        sqd["Calculation mode"] = "pblk"
        for i in range(a_tms):
            sqd["At. dens."] = rho
            sqd["R_c"] = rcc
            sSQ, crvs, ks = sqc.calc_sq_Stetsiv(exq, exi, sqd, clb)
            if not clb:
                return
            bg0 = crvs[1][0] * ks
            rho, rcc = sqc.calc_rho_rc(exq, sSQ, bg0, pars, sear, prc, rcc)
            if not clb(1):
                return
            if plot is not None:
                rho_col.append((rho, rcc))
        self.save_state()
        if plot is not None:
            rhoa, rca = zip(*rho_col)
            its = np.arange(1, len(rca) + 1)
            plts = [(its, rhoa, 1), (its, rca, 2)]
            pldat = plot.set_data(PN_ADE, plts, _("Iteration"),
                                  _(r'At. dens., $\AA^{-3}$'), 'N')
            pldat.discards.add("liq samp")
            pldat.set_info(u"""density = %g (blue)\n
cutoff = %g (green)\n
""" % (rho, rcc))
            pldat.journal.log("calc_roho_rc: \\rho: %g; r_c%g: %g" %
                              (rho, rcc))
            plot.plot_dataset(PN_ADE)
        return rho, rcc


def save_sq_file(mobj):
    if "SSF" not in mobj.data:
        return
    wild = _("dat (*.dat)|*.dat|Extended SQ (*.esq)|*.esq")
    fd = wx.FileDialog(
        mobj, message=_("Save structure factor"),
        style=wx.FD_SAVE, wildcard=wild, defaultDir=mobj.prev_dir)
    if fd.ShowModal() == wx.ID_OK:
        fnam = fd.GetPath()
        findex = fd.GetFilterIndex()
        if findex == 0:
            if fnam[-4:] != '.dat':
                fnam += '.dat'
        else:
            if fnam[-4:] != '.esq':
                fnam += '.esq'
        if osp.isfile(fnam) and  \
                wx.MessageBox(_(u"""File \u201C%s\u201D already exists.
Rewrite it?""") % osp.basename(fnam), PROG_NAME, wx.YES_NO |
                              wx.ICON_EXCLAMATION) == wx.NO:
                fd.Destroy()
                return
        mobj.prev_dir = fd.GetDirectory()
        if findex == 0:
            otpl = mobj.data["SSF"]
        else:
            exq, csq, sqd = mobj.data["SSF"][:3]
            els = sqd["Elements"]
            otpl = sqc.esq_calc(exq, csq, els) + (sqd,)
        from core.file import save_dat
        save_dat(fnam, otpl)
    fd.Destroy()
