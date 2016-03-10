#!/usr/bin/env python
"db interface"
# wxRays (C) 2013-2016 Serhii Lysovenko
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

import sqlite3 as sql
from os.path import isfile
import numpy as np
import locale as loc
ELNUMS = {
    "D": 1, "H": 1, "T": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7,
    "O": 8, "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
    "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22,
    "V": 23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29,
    "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34, "Br": 35, "Kr": 36,
    "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Tc": 43,
    "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50,
    "Sb": 51, "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57,
    "Ce": 58, "Pr": 59, "Nd": 60, "Pm": 61, "Sm": 62, "Eu": 63, "Gd": 64,
    "Tb": 65, "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69, "Yb": 70, "Lu": 71,
    "Hf": 72, "Ta": 73, "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78,
    "Au": 79, "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83, "Po": 84, "At": 85,
    "Rn": 86, "Fr": 87, "Ra": 88, "Ac": 89, "Th": 90, "Pa": 91, "U": 92,
    "Np": 93, "Pu": 94, "Am": 95, "Cm": 96, "Bk": 97, "Cf": 98, "Es": 99,
    "Fm": 100, "Md": 101, "No": 102, "Lr": 103, "Rf": 104, "Db": 105,
    "Sg": 106, "Bh": 107, "Hs": 108, "Mt": 109, "Ds": 110, "Ln": 111}


def formula_markup(fstr, wiki=False):
    formula = fstr.replace("!", u"\u00d7")
    res = u""
    for item in formula.split():
        if item in ['(', ')', u'\u00d7', ','] or\
                item[0].isdigit() or item.startswith(u"\u00d7"):
            res += item
            continue
        if item.startswith(')'):
            res += ")<sub>%s</sub>" % item[1:]
            continue
        epos = 0
        while epos < len(item) and item[epos].isalpha():
            epos += 1
        if epos:
            while epos and item[:epos] not in ELNUMS:
                epos -= 1
            if item[:epos] in ELNUMS:
                res += "%s<sub>%s</sub>" % (item[:epos], item[epos:])
            else:
                res += item
    res = res.replace(u"\u00d7", u" \u00d7 ")
    if wiki:
        res = res.replace("<sub>", "_{")
        res = res.replace("</sub>", "}")
    return res.replace(",", ", ")


def switch_number(number):
    if type(number) is int:
        unum = u"%.6d" % number
        return unum[0:2] + "-" + unum[2:]
    else:
        return int(number.replace("-", ""))


class Database:
    "Powder diffraction database class"
    def __init__(self, path):
        self.connection = None
        if not isfile(path):
            return
        try:
            self.connection = sql.connect(path)
        except sql.Error as e:
            return

    def __bool__(self):
        return self.connection is not None

    __nonzero__ = __bool__

    def execute(self, command, commit=True):
        cursor = self.connection.cursor()
        cursor.execute(command)
        if commit:
            self.connection.commit()
        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, tp, val, tb):
        self.close()

    def select_bruto(self, req):
        spl = req.split(";")
        spl1 = spl[0].split()
        must = [ELNUMS[x] for x in spl1 if x in ELNUMS]
        if len(spl) > 1:
            spl1 = spl[1].split()
            can = [ELNUMS[x] for x in spl1 if x in ELNUMS]
            if spl1 == ["*"]:
                can = None
        else:
            can = []
        if not must and not can:
            return []
        minstr = """SELECT cid, name, formula, quality FROM about INNER JOIN
        (SELECT cid as icid FROM elements GROUP BY cid HAVING SUM(%s) = %d)
        ON cid = icid"""
        mcon = "WHEN enum IN (%s) THEN 1" % ",".join(map(str, must))
        msum = len(must)
        if can is None:
            scon = "CASE %s ELSE 0 END" % mcon
        elif can:
            scon = "case when enum in (%s) then 0 %s else -1" % (
                ",".join(map(str, can)), mcon)
        else:
            scon = "CASE %s ELSE -1 END" % mcon
        return self.execute(minstr % (scon, msum))

    def reflexes(self, cid, hkl=False):
        hkl = ", h, k, l" if hkl else ""
        return self.execute(
            "select d, intens%s from reflexes where cid=%d "
            "ORDER BY d" % (hkl, cid), False)

    def quality(self, cid):
        return self.execute(
            "SELECT quality FROM about WHERE cid=%d" % cid, False)[0][0]

    def spacegroup(self, cid):
        return self.execute(
            "SELECT sgroup FROM about WHERE cid=%d" % cid, False)[0][0]

    def get_di(self, cid, xtype="A^{-1}", wavel=None):
        reflexes = self.reflexes(cid)
        if not reflexes:
            return [], []
        dis = np.array(reflexes, "f").transpose()
        if xtype == "A^{-1}":
            x = (2. * np.pi) / dis[0]
        elif xtype == "A":
            x = dis[0]
        elif xtype == "sin(\\theta)":
            x = wavel / 2. / dis[0]
        elif xtype == "\\theta":
            x = np.arcsin(wavel / 2. / dis[0]) / np.pi * 180.
        elif xtype == "2\\theta":
            x = np.arcsin(wavel / 2. / dis[0]) / np.pi * 360.
        else:
            raise ValueError("Unknown x axis type: %s" % xtype)
        intens = dis[1]
        if intens.max() == 999.:
            for i in (intens == 999.).nonzero():
                intens[i] += 1.
            intens /= 10.
        return x, intens

    def wiki_di(self, cid, xtype, wavels, pld=None):
        return Wiki_card(self, cid, xtype, wavels, pld)

    def comment(self, cid):
        cmt = self.execute(
            "SELECT comment FROM about WHERE cid=%d" % cid, False)
        if not cmt:
            return
        cmt = cmt[0][0]
        if not cmt:
            return
        dcoduns = {"BF": "b", "IT": "i"}
        for cod, val in eval(cmt):
            val = val.decode("utf8")
            if '\\' in val:
                coduns = []
                spos = 0
                epos = val.find('\\')
                rval = u""
                while epos >= 0:
                    rval += val[spos:epos]
                    bilcode = val[epos + 1:epos + 3]
                    if bilcode.isupper() and bilcode.isalpha():
                        if bilcode == "RG":
                            for codun in coduns:
                                rval += "</%s>" % codun
                        elif bilcode in dcoduns:
                            codun = dcoduns[bilcode]
                            rval += "<%s>" % codun
                            coduns.insert(0, codun)
                        else:
                            print("Warning: No such dcodun '%s'" % bilcode)
                        spos = epos + 3
                    else:
                        spos = epos + 1
                        epos = val.find("\\", spos)
                        rval += formula_markup(val[spos:epos])
                        spos = epos + 1
                    epos = val.find("\\", spos)
                val = rval + val[spos:]
            yield cod, val

    def formula_markup(self, cid, wiki=False):
        fstr, = self.execute("SELECT formula FROM about WHERE cid=%d" % cid)[0]
        if not fstr:
            return ''
        else:
            return formula_markup(fstr, wiki)

    def name(self, cid):
        return self.execute("SELECT name FROM about WHERE cid=%d" % cid)[0][0]

    def cell_params(self, cid):
        return self.execute("SELECT param, value FROM cellparams "
                            "WHERE cid=%d ORDER BY param" % cid, False)

    def citations(self, cid):
        return self.execute(
            "SELECT source, vol, page, year, authors FROM citations LEFT JOIN "
            "sources ON citations.sid=sources.sid WHERE cid=%d "
            "ORDER BY year DESC" % cid, False)


class Wiki_card:
    def __init__(self, db, cid, xtype, wavels, pld):
        self.ctp = db, cid, xtype, wavels
        if pld is not None:
            self.xy = pld.plots[0][:2]
        else:
            self.xy = None

    def __str__(self):
        db, cid, xtype, wavels = self.ctp
        pos = db.get_di(cid, xtype, wavels[0])[0]
        refl = db.reflexes(cid, True)
        xt = {'\\theta': u"\u03b8", 'A^{-1}': u"\u212b^{-1}",
              'sin(\\theta)': u"sin(\u03b8)", 'A': u"\u212b",
              '2\\theta': u"2\u03b8"}[xtype]
        uformula = db.formula_markup(cid, True)
        table = ["=== %s ===\n" % db.name(cid),
                 "%s: %s\n" % (switch_number(cid), uformula),
                 "{|", "! x (%s)" % xt,
                 u"! d (\u212b)", "! I"]
        hkl_col = any([i[2] is not None for i in refl]) > 2
        if hkl_col:
            table.append("! hkl")
        for p, r in zip(pos, refl):
            table.append("|-")
            table.append("\n".join(["| %s" % loc.format("%g", i)
                                    for i in ((p,) + r[:2])]))
            if r[2] is not None:
                table.append("| %d %d %d" % r[2:])
        table.append("|}")
        if self.xy is not None:
            for wavel in wavels:
                pos = db.get_di(cid, xtype, wavel)[0]
                self.gnuplot_tail(table, pos, refl, hkl_col, uformula)
        return u"\n".join(table)

    def gnuplot_tail(self, table, pos, refl, hkl_col, uformula):
        table.append("----")
        plotpos = []
        x, y = self.xy
        for p, r in zip(pos, refl):
            if p < x[0] or p > x[-1]:
                continue
            for xp, xv in enumerate(x):
                if xv >= p:
                    break
            xp1 = xp - 1
            y0 = y[xp1] + (p - x[xp1]) * (y[xp] - y[xp1]) / (xv - x[xp1])
            plotpos.append((p, y0) + r[2:])
        for p in plotpos:
            table.append("set arrow from %g, %g rto 0, ll nohead\n"
                         % p[:2])
            name = uformula
            if len(p) > 2:
                name += " (%d %d %d)" % p[2:]
            table.append("set label \"%s\" at %g, %g + ll rotate\n"
                         % ((name,) + p[:2]))
