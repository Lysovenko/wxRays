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
        self.treaters = {
            'label': self.label,
            'text': self.text,
            'spin': self.spin,
            'button': self.button,
            'radio': self.radio,
            'line': self.line
        }

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
        self.actors['table_new']()
        for r in table:
            if r.tag != "tr":
                raise KeyError("table must contain only raws")
            self.actors["table_next_raw"]()
            for c in r:
                if c.tag != "td":
                    raise KeyError("raw must contain only cells")
                cont = self.treaters[c[0].tag](c[0])
                align = c.get('align')
                colspan = c.get('colspan')
                if colspan is not None:
                    colspan = self.integer(colspan)
                rowspan = c.get('rowspan')
                if rowspan is not None:
                    rowspan = self.integer(rowspan)
                expand = self.boolean(c.get('expand'))
                border = c.get('border')
                if border is not None:
                    border = self.integer(border)
                self.actors["table_put_cell"](cont, align, colspan,
                                              rowspan, expand, border)
        self.actors['table_end']()

    def label(self, label):
        rename = label.get("rename")
        if rename:
            return self.actors['get_label'](self.data.get(rename, label.text))
        else:
            return self.actors['get_label'](label.text)

    def text(self, text):
        props = {}
        for i in ("value", "validator"):
            p = text.get(i)
            if p in self.data:
                p = self.data[value]
            props[i] = p
        return self.actors['get_text'](**props)

    def spin(self, spin):
        props = {}
        for i in ("begin", "end", "value"):
            props[i] = self.integer(spin.get(i))
        return self.actors['get_spin'](**props)

    def button(self, button):
        b_type = button.get('type')
        default = self.boolean(button.get('default'))
        return self.actors['get_button'](b_type, default=default)

    def radio(self, radio):
        vertical = self.boolean(radio.get('vertical'))
        title = self.data.get(radio.get("rename")) or radio.get('title')
        default = self.integer(radio.get('default', 0))
        onchange = radio.get('onchange')
        if onchange is not None:
            onchange = self.data[onchange]
        options = [self.data.get(i.get("rename")) or i.text for i in radio]
        return self.actors['get_radio'](
            title, options, default, vertical, onchange)

    def integer(self, param):
        try:
            res = int(param)
        except ValueError:
            res = self.data[param]
        if type(res) is not int:
            raise ValueError("%s must be integer" % param)
        return res

    def boolean(self, param):
        if param not in {'True', 'False', None}:
            res = self.data[param]
        else:
            res = param == 'True'
        return res

    def line(self, line):
        return self.actors['get_line']()


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
    p.set_actors({
        'set_title': lambda x: print('Title:', x),
        'table_next_raw': lambda: print('='*25),
        'table_put_cell': lambda c, a, co, ro, e, b: print(
            '<td al=%s csp=%s rsp=%s exp=%s bor=%s>' %
            (a, co, ro, e, b), c, '</td>'),
        'get_label': lambda l: 'label: %s' % l,
        'get_text': lambda **p: 'text: %s' % p,
        'get_spin': lambda **p: 'spin: %s' % p,
        'get_button': lambda t, default=False:
        'button type=%s, default=%s' % (t, default),
        'get_radio': lambda *r: 'radio: %s' % (r,),
        'get_line': lambda: '-'*20})
    p.set_data({'sqcalc_mode': 0, 'on_mode_change': None, 'pol_spin': 3,
                'sqcalc_optcects': 3, "ord_r_spin": 3, "rc_num": 5})
    p.play()
