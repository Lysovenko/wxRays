#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Alternative for gettext"
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


import wx
import __builtin__
from os import stat
from os.path import dirname, realpath, isfile
from marshal import dump, load


def introduce(data):
    "Addons Entry point"
    dict_fn = APP_SETT.get_home("alt_mo.dmp")
    APP_SETT.declare_section("ALT_GETTEXT")
    pofn = eval(APP_SETT.get("po_file", "''", "ALT_GETTEXT"))
    __builtin__.__dict__["_"] = AltGT(get_podict(pofn))
    adat = data["window"].addons_data
    menu = data["menu"]
    for i in APP_SETT.addons.terminate(adat, True):
        menu.remove_add_id(i)
    mid = data["id"]
    for desc in APP_SETT.addons.descriptions:
        if desc["id"] == mid:
            break
    desc["isactive"] = False
    APP_SETT.addons.introduce(adat)
    desc["isactive"] = True
    menu.replay_actions()


class Config:
    def __init__(self, data):
        self.data = data

    def get_visual(self, parent):
        import wx.lib.filebrowsebutton as filebrowse
        pof = eval(APP_SETT.get("po_file", "''", "ALT_GETTEXT"))
        if pof:
            sdir = dirname(pof)
        else:
            sdir = dirname(realpath(__file__))
        self.fbb = filebrowse.FileBrowseButton(
            parent, labelText=_("PO file:"), buttonText=_("Open"),
            dialogTitle=_("Open the po file"), fileMask=_("po files|*.po"),
            fileMode=wx.OPEN, startDirectory=sdir, size=wx.Size(300, -1))
        return self.fbb

    def configure(self):
        dict_fn = APP_SETT.get_home("alt_mo.dmp")
        fnam = self.fbb.GetValue()
        APP_SETT.set("po_file", repr(fnam), "ALT_GETTEXT")
        __builtin__.__dict__["_"] = AltGT(get_podict(fnam))


class AltGT:
    "alternative for gettext"
    def __init__(self, data):
        self.data = data

    def __call__(self, wrd):
        wrd = unicode(wrd)
        return self.data.get(wrd, wrd)


def get_podict(fname):
    altmo = APP_SETT.get_home("alt_mo.dmp")
    res = {}
    if isfile(fname):
        if not isfile(altmo) or stat(fname).st_mtime > stat(altmo).st_mtime:
            with open(fname) as pof:
                res = pof2dict(pof)
            with open(altmo, "wb") as mof:
                dump(res, mof)
            return res
    if isfile(altmo):
        with open(altmo, "rb") as mof:
            res = load(mof)
    return res


def pof2dict(pof):
    fuzzy = False
    msgidon = False
    msgstr = ""
    odict = {}
    for line in pof:
        if line.startswith("#"):
            if line.startswith("#, ") and ", fuzzy" in line:
                fuzzy = True
            continue
        if line.startswith("msgid "):
            msgidon = True
            msgid = eval(line[6:])
        if line.startswith("msgstr "):
            msgidon = False
            msgstr = eval(line[7:])
        if line.startswith('"'):
            if msgidon:
                msgid += eval(line)
            else:
                msgstr += eval(line)
        if line.isspace():
            if fuzzy:
                fuzzy = False
            elif msgstr:
                odict[msgid.decode("utf-8")] = msgstr.decode("utf-8")
    if msgstr and not fuzzy:
        odict[msgid.decode("utf-8")] = msgstr.decode("utf-8")
    return odict
