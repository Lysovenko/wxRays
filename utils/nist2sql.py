#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

from NIST import NIST_Card, dump_card
from sys import argv, stderr

if __name__ == "__main__":
    fobj = open(argv[1])
    print("""PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;""")
    print("CREATE TABLE elements_ind (cid int, enum int);")
    print("CREATE TABLE reflexes (cid INT, d REAL, intens REAL,"
          " h INT, k INT, l INT);")
    pos = 0
    nextp = 1
    while pos >= 0:
        print (pos, file=stderr)
        card = NIST_Card()
        ppos = pos
        pos = card.set_by_NIST_file(fobj, ppos)
        dump_card(card)
    fobj.close()
    print("COMMIT;")
