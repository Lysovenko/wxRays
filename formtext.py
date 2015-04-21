#!/usr/bin/env python
# -*- coding: utf-8 -*-
"text formater"
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


import re
import locale as loc

_escapes = {ord('\r'): None, ord('&'): u'&amp;',
            ord('<'): u'&lt;', ord('>'): u'&gt;'}


def wiki2html(wiki):
    wiki = unicode(wiki).translate(_escapes)
    for i in xrange(1, 7):
        w = '=' * i
        p = re.compile(r'^%s\s+([^=\[]*?)\s+%s' % (w, w), re.M | re.U)
        wiki = p.sub('<h%d>\\1</h%d>' % (i, i), wiki)
    p = re.compile(r"^----+$", re.M | re.U)
    wiki = p.sub('<hr>', wiki)
    p = re.compile("(?<!')'''''([^']+)'''''(?!')",  re.M | re.U)
    wiki = p.sub(r"<strong><em>\1</em></strong>", wiki)
    p = re.compile("(?<!')'''([^']+)'''(?!')",  re.M | re.U)
    wiki = p.sub(r"<strong>\1</strong>", wiki)
    p = re.compile("(?<!')''([^']+)''(?!')",  re.M | re.U)
    wiki = p.sub(r"<em>\1</em>", wiki)
    # unordered
    p = re.compile(r"^\*\s*(.*)", re.M | re.U)
    wiki = p.sub(r"<li>\1</li>", wiki)
    p = re.compile(r"\n\n<li>", re.M | re.U | re.S)
    wiki = p.sub("\n<ul>\n<li>", wiki)
    p = re.compile(r"<\/li>\n(?!<li>)", re.M | re.U | re.S)
    wiki = p.sub("</li>\n</ul>", wiki)
    # ordered
    p = re.compile(r"^#[:]?[#]*\s*(.*)", re.M | re.U)
    wiki = p.sub(r"<li>\1</li>", wiki)
    p = re.compile(r"\n\n<li>", re.M | re.U | re.S)
    wiki = p.sub("\n<ol>\n<li>", wiki)
    p = re.compile(r"<\/li>\n(?!<li>)", re.M | re.U | re.S)
    wiki = p.sub("</li>\n</ol>", wiki)
    # paragraph
    p = re.compile(r"(?:(?<=\A)|(?<=\n\n))([^#=\*\{].*?)(?:(?=\n\n+)|(?=\Z))",
                   re.M | re.U | re.S)
    wiki = p.sub(r"<p>\1</p>", wiki)
    p = re.compile(r"<p><hr><\/p>")
    wiki = p.sub(r"<hr>", wiki)
    # table
    p = re.compile(r"^\{\|", re.M | re.U)
    wiki = p.sub("<table><tr>", wiki)
    p = re.compile(r"^\|-", re.M | re.U)
    wiki = p.sub("</tr><tr>", wiki)
    p = re.compile(r"^!\s(.*)", re.M | re.U)
    wiki = p.sub("<th>\\1</th>", wiki)
    p = re.compile(r"^\|\s(.*)", re.M | re.U)
    wiki = p.sub("<td>\\1</td>", wiki)
    p = re.compile(r"^\|\}", re.M | re.U)
    wiki = p.sub("</tr></table>", wiki)
    p = re.compile(r"\^\{([^}]*)\}", re.U)
    wiki = p.sub("<sup>\\1</sup>", wiki)
    p = re.compile(r"_\{([^}]*)\}", re.U)
    wiki = p.sub("<sub>\\1</sub>", wiki)
    return wiki


def poly1d2wiki(coefs):
    deg = len(coefs) - 1
    jts = ["%s x^{%d}" % (loc.format("%g", j), deg - i)
           for i, j in enumerate(coefs)]
    res = u' + '.join(jts)
    res = res[:-6]
    p = re.compile(r"\+\ -", re.U)
    res = p.sub("- ", res)
    p = re.compile(r"\^\{1\}", re.U)
    res = p.sub("", res)
    p = re.compile(r"e\+0*(\d*)", re.U)
    res = p.sub(u"\u00d710^{\\1}", res)
    p = re.compile(r"e-0*(\d*)", re.U)
    res = p.sub(u"\u00d710^{-\\1}", res)
    return res
