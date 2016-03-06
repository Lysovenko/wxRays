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


class Database:
    "Powder diffraction database class"
    def __init__(self, path):
        self.connection = None
        try:
            self.connection = sql.connect(path)
        except sql.Error as e:
            return

    def __bool__(self):
        return self.connection is not None

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
        must = [ELEMENTS[x] for x in spl1 if x in ELEMENTS]
        if len(spl) > 1:
            spl1 = spl[1].split()
            can = [ELEMENTS[x] for x in spl1 if x in ELEMENTS]
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

# SELECT cid, name, formula, quality FROM about INNER JOIN (SELECT cid as icid FROM elements GROUP BY cid HAVING SUM(CASE WHEN enum IN () THEN 0 WHEN enum IN (8, 74) THEN 1 ELSE -1 END) = 2) ON cid = icid ;
 
#SELECT cid FROM elements GROUP BY cid HAVING SUM(CASE WHEN enum IN (1) THEN 0 WHEN enum IN (8, 74) THEN 1 ELSE -1 END) = 2;
