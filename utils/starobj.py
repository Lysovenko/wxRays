#!/usr/bin/env python3
"STAR object"
# starobj (C) 2016 Serhii Lysovenko
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

import re
import pyparsing

class StarObj(dict):
    def __init__(self, initor=None):
        dict.__init__(self)
        if type(initor) is str:
            self.update(initor)

    def update(self, upstr):
        text_block = None
        for line in upstr.splitlines():
            if text_block is not None:
                if line.strip() == ';':
                    pass
                else:
                    text_block.append(line)
            lcl = line.lovercase().strip()
            if lcl.startswith('loot_'):
                pass
