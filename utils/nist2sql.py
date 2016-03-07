#!/usr/bin/env python3
"NIST database format to SQL convertor"
# nist2sql (C) 2016 Serhii Lysovenko
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
from sys import argv, stderr


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
BILCODES = {"AP": "\u2248", "DA": "\u2020", "DD": "\u2021", "DE": "\u00b0",
            "GA": "\u03b1", "GB": "\u03b2", "GC": "\u03c8", "GD": "\u03b4",
            "GE": "\u03b5", "GF": "\u03c6", "GG": "\u03b3", "GH": "\u03b7",
            "GI": "\u03b9", "GJ": "\u03be", "GK": "\u03ba", "GL": "\u03bb",
            "GM": "\u03bc", "GN": "\u03bd", "GO": "\u03bf", "GP": "\u03c0",
            "GR": "\u03c1", "GS": "\u03c3", "GT": "\u03c4", "GU": "\u03b8",
            "GV": "\u03c9", "GX": "\u03c7", "GY": "\u03c5", "GZ": "\u03b6",
            "ND": "\u2248", "NE": "\u2264", "NF": "\u2265", "NO": "\u2116",
            "PD": "\u2022", "PG": "\u00a7", "PM": "\u00b1", "SE": "\u00a7",
            "VD": "\u0394", "VS": "\u03a3", "VV": "\u03a9"}


def replace_bilcode(sstr):
    spos = 0
    epos = sstr.find("$", spos)
    res = ""
    while epos >= 0:
        res += sstr[spos:epos]
        bilcode = sstr[epos + 1:epos + 3]
        if bilcode in BILCODES:
            res += BILCODES[bilcode]
        else:
            res += "$" + bilcode
        spos = epos + 3
        epos = sstr.find("$", spos)
    return res + sstr[spos:]


class NIST_Card:
    "Support for NIST*AIDS-83 format"
    def __init__(self):
        self.content = []
        self.name = None
        self.formula = None
        self.reflexes = None
        self.number = None
        self.quality = None
        self.comment = None
        self.ref = None
        self.cellparams = None
        self.spc_grp = "NULL"

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
                while epos and fel[:epos] not in ELNUMS:
                    epos -= 1
                if fel[:epos] in ELNUMS:
                    els.append(ELNUMS[fel[:epos]])
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
            self.content.append((ELNUMS[elem[:pos]], quan))

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

    def set_by_NIST_file(self, fobj, pos):
        'read card fields'
        fobj.seek(pos * 80)
        buf = fobj.read(80)
        if not buf:
            return - 1
        snum = buf[72:79]
        self.number = int(buf[72:78])
        self.quality = buf[71] + buf[78]
        while snum == buf[72:79]:
            row_type = buf[79]
            if row_type == '1':
                if buf[0:51].strip():
                    cellparams = []
                    for i in range(0, 27, 9):
                        sst = buf[i:i + 9].strip().replace(',', '')
                        try:
                            cellparams.append(sst and float(sst) or None)
                        except ValueError:
                            print("Bad Float", sst, file=stderr)
                    for i in range(27, 51, 8):
                        sst = buf[i:i + 8].strip()
                        cellparams.append(sst and float(sst) or None)
                    self.cellparams = tuple(cellparams)
            elif row_type == '3':
                sgr = buf[0:10].strip()
                self.spc_grp = "'%s'" % sgr if sgr else "NULL"
            elif row_type == '8':
                self.set_content_buf(buf)
            elif row_type == '7':
                if not self.formula:
                    self.formula = buf[:66].rstrip()
                elif buf[68] != 'S':
                    self.formula += ' ' + buf[:66].rstrip()
            elif row_type == 'B':
                if not self.comment:
                    self.comment = []
                csec = buf[67:69]
                tbc = buf[69] == 'C'
                cval = buf[:67].rstrip()
                if '$' in cval:
                    cval = replace_bilcode(cval)
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
            elif row_type == '9':
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
            elif row_type == 'I':
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
            return ""
        if '$' not in self.name:
            return str(self.name)
        return replace_bilcode(self.name)

    def dump_sql(self, codens):
        num = self.number
        if not self.reflexes:
            return
        if not self.content:
            contains = self.get_formula_elements()
            if not contains:
                return
            self.content = [(i, 0) for i in contains]
        formula = self.formula if self.formula else ""
        name = self.get_uname().replace("'", "''")
        comment = "'%s'" % repr(self.comment).replace("'", "''") if \
                  self.comment else "NULL"
        sql("INSERT INTO about VALUES(%d, '%s', '%s', %s, '%s', %s)" % (
            num, name, formula, self.spc_grp, self.quality, comment))
        for i, j in enumerate(self.cellparams) if self.cellparams else ():
            if j is not None:
                sql("insert into cellparams values(%d, %d, %g)" %
                    (num, i, j))
        for i in self.ref if self.ref else ():
            cmd = "INSERT INTO citations VALUES(%d, %d" % (
                num, codens[i["code"]])
            for j in ("V", "P", "Y", "names"):
                if i[j]:
                    if j == "Y":
                        cmd += ", %s" % i[j]
                    else:
                        cmd += ", '%s'" % i[j].replace("'", "''")
                else:
                    cmd += ", NULL"
            sql(cmd + ")")
        for i in self.content:
            sql("INSERT INTO elements VALUES(%d, %d, %d)" % ((num,) + i))
        for i in self.reflexes:
            if len(i) == 2:
                sql("INSERT INTO reflexes VALUES(%d, %g, %g, NULL, NULL, "
                    "NULL)" % ((num,) + i))
            else:
                sql("INSERT INTO reflexes VALUES(%d, %g, %g, %d, %d, %d)" %
                    ((num,) + i))


def dump_codens(codest):
    res = {}
    if not osp.isfile(codest):
        return res
    sid = 0
    with open(codest, "rb") as fobj:
        buf = fobj.read(80)
        while buf:
            code = buf[:6].decode()
            ref = buf[7:].decode().strip().replace("'", "''")
            sql("INSERT INTO sources VALUES(%d, '%s');" % (sid, ref))
            res[code] = sid
            sid += 1
            buf = fobj.read(80)
    return res


if __name__ == "__main__":
    import os.path as osp
    import sqlite3
    fobj = open(argv[1])
    fobj.seek(0, 2)
    codest = osp.dirname(argv[1])
    codest = osp.join(codest, "codens.dat")
    epo = fobj.tell()
    lines = epo / 80
    pos = 0
    nextp = 1
    shown = -1
    connection = sqlite3.connect(argv[2])
    cursor = connection.cursor()
    global sql
    sql = cursor.execute
    sql("CREATE TABLE elements (cid INT, enum INT, quantity INT)")
    sql("CREATE TABLE reflexes (cid INT, d REAL, intens INT,"
        " h INT, k INT, l INT)")
    sql("CREATE TABLE about (cid INT, name VARCHAR, formula VARCHAR,"
        " sgroup VARCHAR, quality VARCHAR, comment TEXT)")
    sql("CREATE TABLE cellparams (cid INT, param INT, value REAL)")
    sql("CREATE TABLE citations (cid INT, sid INT, vol VARCHAR, page VARCHAR,"
        "  year INT, authors VARCHAR)")
    sql("CREATE TABLE sources (sid INT, source VARCHAR)")
    codens = dump_codens(codest)
    while pos >= 0:
        curp = int(pos / lines * 100)
        if curp > shown:
            shown = curp
            print("%d %%" % curp, file=stderr)
        card = NIST_Card()
        pos = card.set_by_NIST_file(fobj, pos)
        card.dump_sql(codens)
    fobj.close()
    connection.commit()
    connection.close()
