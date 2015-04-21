#!/usr/bin/env python
# -*- coding: utf-8 -*-
"powder diffraction file version 2 to python data"
# wxRays (C) 2014 Serhii Lysovenko
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

import numpy as np
import locale as loc

CS_LEN = 80
CS_END_POS = 79
CS_NUM_LEN = 6
CS_NUM_START = 72
CS_PAT_SEC = 23
CS_PAT_N_SEC = 3
CS_PAT_D = 7
CS_PAT_I = 3
CS_PAT_I_MARK = 1
CS_PAT_HKL = 3
CS_NAME_TYPE = 68
CS_CONTINUE = 69
CS_TYPE = 78
CS_STATUS = 71
ELEMENTS = ['H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na',
            'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti',
            'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As',
            'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru',
            'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs',
            'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy',
            'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir',
            'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra',
            'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es',
            'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
            'Ln', 'D', 'T']
BILCODES = {"AP": u"\u2248", "DA": u"\u2020", "DD": u"\u2021", "DE": u"\u00b0",
            "GA": u"\u03b1", "GB": u"\u03b2", "GC": u"\u03c8", "GD": u"\u03b4",
            "GE": u"\u03b5", "GF": u"\u03c6", "GG": u"\u03b3", "GH": u"\u03b7",
            "GI": u"\u03b9", "GJ": u"\u03be", "GK": u"\u03ba", "GL": u"\u03bb",
            "GM": u"\u03bc", "GN": u"\u03bd", "GO": u"\u03bf", "GP": u"\u03c0",
            "GR": u"\u03c1", "GS": u"\u03c3", "GT": u"\u03c4", "GU": u"\u03b8",
            "GV": u"\u03c9", "GX": u"\u03c7", "GY": u"\u03c5", "GZ": u"\u03b6",
            "ND": u"\u2248", "NE": u"\u2264", "NF": u"\u2265", "NO": u"\u2116",
            "PD": u"\u2022", "PG": u"\u00a7", "PM": u"\u00b1", "SE": u"\u00a7",
            "VD": u"\u0394", "VS": u"\u03a3", "VV": u"\u03a9"}


class ElFilter:
    def __init__(self, elstr=''):
        self.must = None
        self.can = None
        if elstr:
            self.reset_string(elstr)

    def reset_string(self, elstr):
        spl = elstr.split(";")
        spl1 = spl[0].split()
        must0 = [ELEMENTS.index(x) for x in spl1 if x in ELEMENTS]
        must = []
        for elm in must0:
            if elm not in must:
                must.append(elm)
        self.must = must
        if len(spl) > 1:
            spl1 = spl[1].split()
            can0 = [ELEMENTS.index(x) for x in spl1 if x in ELEMENTS]
            can = []
            for elm in can0:
                if elm not in can:
                    can.append(elm)
            if spl1 == ["*"]:
                self.can = None
            else:
                self.can = can
        else:
            self.can = []

    def __call__(self, seq):
        seqc = list(seq)
        try:
            for i in self.must:
                seqc.remove(i)
        except ValueError:
            return False
        if self.can is None:
            return True
        for i in seqc:
            if i not in self.can:
                return False
        return True

    def __nonzero__(self):
        return bool(self.must or self.can)


def string_card(fobj, pos):
    'read datafile fields and set content'
    fobj.seek(pos * 80)
    buf = fobj.read(80)
    if not buf:
        return - 1
    snum = buf[72:79]
    res = ''
    while buf and snum == buf[72:79]:
        res += buf + '\n'
        buf = fobj.read(80)
    return res


class NIST_Card:
    "Support for NIST*AIDS-83 format"
    def __init__(self):
        self.content = []
        self.name = None
        self.formula = None
        self.reflexes = None
        self.deleted = None
        self.number = None
        self.quality = None
        self.comment = None
        self.ref = None
        self.cellparams = None
        self.spc_grp = None

    def get_dict(self):
        'return card as Python dictionary'
        resd = {}
        for item in ['content', 'name', 'formula', 'reflexes', 'number']:
            val = eval('self.' + item)
            if val:
                resd[item] = val
        return resd

    def get_formula_elements(self):
        'list of elements from formula of compound'
        if not self.formula:
            return None
        spl = self.formula.split()
        els = []
        for fel in spl:
            epos = 0
            while epos < len(fel) and fel[epos].isalpha():
                epos += 1
            if epos:
                while epos and fel[:epos] not in ELEMENTS:
                    epos -= 1
                if fel[:epos] in ELEMENTS:
                    els.append(ELEMENTS.index(fel[:epos]))
        els.sort()
        ind = 1
        while ind < len(els):
            if els[ind] == els[ind - 1]:
                els.pop(ind)
            else:
                ind += 1
        return els

    def set_content_buf(self, buf):
        'set ciontent from buffer'
        stra = buf[:65].split()
        for elem in stra:
            pos = 1
            elen = len(elem)
            while pos < elen and elem[pos].isalpha():
                pos += 1
            try:
                quan = int(elem[pos:])
            except ValueError:
                quan = 1
            self.content.append((ELEMENTS.index(elem[:pos]), quan))

    def set_reflexes_buf(self, buf):
        'set reflexes'
        if not self.reflexes:
            self.reflexes = []
        for item in (0, 23, 46):
            try:
                reflex = float(buf[item:item + 7])
            except ValueError:
                continue
            intens = int(buf[item + 7:item + 10])
            try:
                plane = buf[item + 11:item + 20]
                plane = [int(plane[x:x + 3]) for x in (0, 3, 6)]
            except ValueError:
                reflex = (reflex, intens)
            else:
                reflex = tuple([reflex, intens] + plane)
            self.reflexes.append(reflex)

    def get_di(self, xtype='A^{-1}', wavel=None):
        if not self.reflexes:
            return [], []
        dis = np.array([(x[0], x[1]) for x in self.reflexes], 'f').transpose()
        if xtype == 'A^{-1}':
            x = (2. * np.pi) / dis[0]
        elif xtype == 'A':
            x = dis[0]
        elif xtype == 'sin(\\theta)':
            x = wavel / 2. / dis[0]
        elif xtype == '\\theta':
            x = np.arcsin(wavel / 2. / dis[0]) / np.pi * 180.
        elif xtype == '2\\theta':
            x = np.arcsin(wavel / 2. / dis[0]) / np.pi * 360.
        else:
            raise ValueError("Unknown x axis type: %s" % xtype)
        intens = dis[1]
        if intens.max() == 999.:
            for i in (intens == 999.).nonzero():
                intens[i] += 1.
            intens /= 10.
        return x, intens

    def set_content_NIST_file(self, fobj, pos):
        'read datafile fields and set content'
        fobj.seek(pos * 80)
        buf = fobj.read(80)
        if not buf:
            return - 1
        snum = buf[72:79]
        self.number = int(buf[72:78])
        self.quality = buf[78]
        self.deleted = buf[71] == 'D'
        while snum == buf[72:79]:
            if buf[79] == '8':
                self.set_content_buf(buf)
            pos += 1
            buf = fobj.read(80)
            if buf == '':
                break
        return pos

    def set_by_NIST_file(self, fobj, pos, reflexes=True, num_only=False):
        'read card fields'
        if not num_only:
            self.__init__()
        fobj.seek(pos * 80)
        buf = fobj.read(80)
        if not buf:
            return - 1
        snum = buf[72:79]
        self.number = int(buf[72:78])
        self.quality = buf[78]
        self.deleted = buf[71] == 'D'
        if num_only:
            return
        while snum == buf[72:79]:
            row_type = buf[79]
            if row_type == '1' and reflexes:
                if buf[0:51].strip():
                    cellparams = []
                    for i in xrange(0, 27, 9):
                        sst = buf[i:i + 9].strip()
                        cellparams.append(sst and float(sst) or None)
                    for i in xrange(27, 51, 8):
                        sst = buf[i:i + 8].strip()
                        cellparams.append(sst and float(sst) or None)
                    self.cellparams = tuple(cellparams)
            elif row_type == '3' and reflexes:
                sgr = buf[0:10].strip()
                if sgr:
                    self.spc_grp = sgr
            elif row_type == '8':
                self.set_content_buf(buf)
            elif row_type == '7':
                if not self.formula:
                    self.formula = buf[:66].rstrip()
                elif buf[68] != 'S':
                    self.formula += ' ' + buf[:66].rstrip()
            elif row_type == 'B' and reflexes:
                if not self.comment:
                    self.comment = []
                csec = buf[67:69]
                tbc = buf[69] == 'C'
                cval = buf[:67].rstrip()
                if self.comment and len(self.comment[-1]) == 3:
                    cval = self.comment[-1][1] + ' ' + cval
                    if tbc:
                        self.comment[-1] = (csec, cval, tbc)
                    else:
                        self.comment[-1] = (csec, cval)
                else:
                    if tbc:
                        self.comment.append((csec, cval, tbc))
                    else:
                        self.comment.append((csec, cval))
            elif row_type == '9' and reflexes:
                if not self.ref:
                    self.ref = []
                code = buf[:6].strip()
                vol = buf[6:10].strip()
                page = buf[10:15].strip()
                year = buf[16:20].strip()
                names = buf[21:67].strip()
                if code:
                    self.ref.append({"code": code, "V": vol, "P": page,
                                     "Y": year, "names": names})
                else:
                    self.ref[-1]["names"] += names
            elif row_type == 'I' and reflexes:
                self.set_reflexes_buf(buf)
            elif row_type == '6' and buf[68] == 'P':
                if self.name:
                    self.name += buf[:68].rstrip()
                else:
                    self.name = buf[:68].rstrip()
            pos += 1
            buf = fobj.read(80)
            if buf == '':
                break
        return pos

    def get_uname(self):
        if self.name is None:
            return u""
        if '$' not in self.name:
            return unicode(self.name)
        spos = 0
        epos = self.name.find("$", spos)
        res = u""
        while epos >= 0:
            res += self.name[spos:epos]
            bilcode = self.name[epos + 1:epos + 3]
            if bilcode in BILCODES:
                res += BILCODES[bilcode]
            spos = epos + 3
            epos = self.name.find("$", spos)
        return res + self.name[spos:]

    def get_unumber(self):
        unum = u"%.6d" % self.number
        return unum[0:2] + "-" + unum[2:]

    def get_uformula(self):
        if self.formula is None:
            return u""
        return self.formula.replace("!", u"\u00d7")

    def get_uformula_markup(self, fstr=None, wiki=False):
        if fstr:
            formula = fstr.replace("!", u"\u00d7")
        else:
            formula = self.get_uformula()
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
                while epos and item[:epos] not in ELEMENTS:
                    epos -= 1
                if item[:epos] in ELEMENTS:
                    res += "%s<sub>%s</sub>" % (item[:epos], item[epos:])
                else:
                    res += item
        res = res.replace(u"\u00d7", u" \u00d7 ")
        if wiki:
            res = res.replace("<sub>", "_{")
            res = res.replace("</sub>", "}")
        return res.replace(",", ", ")

    def get_umcomment(self):
        if self.comment:
            dcoduns = {"BF": "b", "IT": "i"}
            for cod, val in self.comment:
                if '$' in val:
                    spos = 0
                    epos = val.find("$", spos)
                    rval = u""
                    while epos >= 0:
                        rval += val[spos:epos]
                        bilcode = val[epos + 1:epos + 3]
                        if bilcode in BILCODES:
                            rval += BILCODES[bilcode]
                        spos = epos + 3
                        epos = val.find("$", spos)
                    val = rval + val[spos:]
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
                            rval += self.get_uformula_markup(val[spos:epos])
                            spos = epos + 1
                        epos = val.find("\\", spos)
                    val = rval + val[spos:]
                yield cod, val

    def wiki_di(self, xtype, pos, pld=None):
        return Wiki_card(self, xtype, pos, pld)


class Wiki_card:
    def __init__(self, card, xtype, pos, pld):
        self.ctp = card, xtype, pos
        if pld is not None:
            self.xy = pld.plots[0][:2]
        else:
            self.xy = None

    def __str__(self):
        card, xtype, pos = self.ctp
        refl = card.reflexes
        xt = {'\\theta': u"\u03b8", 'A^{-1}': u"\u212b^{-1}",
              'sin(\\theta)': u"sin(\u03b8)", 'A': u"\u212b",
              '2\\theta': u"2\u03b8"}[xtype]
        uformula = card.get_uformula_markup(None, True)
        table = ["=== %s ===\n" % card.get_uname(),
                 "%s: %s\n" % (card.get_unumber(), uformula),
                 "{|", "! x (%s)" % xt,
                 u"! d (\u212b)", "! I"]
        hkl_col = max([len(i) for i in refl]) > 2
        if hkl_col:
            table.append("! hkl")
        for p, r in zip(pos, refl):
            table.append("|-")
            table.append("\n".join(["| %s" % loc.format("%g", i)
                                    for i in ((p,) + r[:2])]))
            if len(r) > 2:
                table.append("| %d %d %d" % r[2:])
        table.append("|}")
        if self.xy is not None:
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
            if plotpos:
                table.append("{|\n| pos\n| val")
                if hkl_col:
                    table.append("! hkl")
                for p in plotpos:
                    table.append("|-\n| %g\n| %g" % p[:2])
                    if len(p) > 2:
                        table.append("| %d %d %d" % p[2:])
                table.append("|}")
            table.append("----")
            for p in plotpos:
                table.append("set arrow from %g, %g rto 0, ll nohead\n"
                             % p[:2])
                name = uformula
                if len(p) > 2:
                    name += " (%d %d %d)" % p[2:]
                table.append("set label \"%s\" at %g, %g + ll rotate\n"
                             % ((name,) + p[:2]))
        return u"\n".join(table)
