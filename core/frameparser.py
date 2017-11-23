#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is the input point to some interesting educational program"
# wxRays (C) 2017 Serhii Lysovenko
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

from __future__ import print_function, absolute_import
import xml.etree.ElementTree as etree


class Puzzle:
    def __init__(self, frame):
        self.frame = frame
        self.actors = None
        self.data = None

    def set_actors(self, actors):
        self.actors = actors

    def set_data(self, data):
        self.data = data

    def play(self):
        for i in self.frame:
            if i.tag == 'title':
                rename = i.get("rename")
                if rename:
                    self.actors['set_title'](self.data.get(rename, i.text))
                else:
                    self.actors['set_title'](i.text)
            elif i.tag == 'table':
                self.play_table(i)

    def play_table(self, table):
        for r in table:
            if r.rag != "tr":
                raise KeyError("table must contain only raws")
            self.actors["table_next_raw"]()
            for c in r:
                if r.rag != "td":
                    raise KeyError("raw must contain only cells")


class Frames:
    def __init__(self, fname):
        self.document = etree.parse(fname).getroot()
        if self.document.tag != "frames":
            raise KeyError("root element myst be \"frames\", %s found" %
                           self.document.tag)
        self.frames = {}
        for i in self.document:
            if i.tag != "frame":
                raise KeyError("Only frame can be child of frames")
            name = i.get('name')
            if name is None:
                raise KeyError("frame must have name")
            if name in self.frames:
                raise KeyError("The name (%s) is not uniqual" % name)
            self.frames[name] = i

    def get(self, name):
        frame = self.frames.get(name)
        if frame is None:
            raise KeyError("No sutch frame '%s'" % name)
        return Puzzle(frame)


if __name__ == '__main__':
    from sys import argv
    f = Frames(argv[1])
    p = f.get(argv[2])
    p.set_actors({'set_title': print})
    p.set_data({})
    p.play()
