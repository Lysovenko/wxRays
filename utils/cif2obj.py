#!/usr/bin/env python3
"CIF file parser"
# cif2obj (C) 2016 Serhii Lysovenko
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

def parsloop(iterable):
    result = {}
    strb = None
    for line in iterable:
        if line.strip() == ";":
            if strb is None:
                strb = ""
            else:
               result[str_item] = strb
               strb = None
        elif strb is not None:
            strb += line
        if line.startswith("_")
