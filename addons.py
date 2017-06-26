#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is Plugin Manager"
# wxRays (C) 2013 Serhii Lysovenko
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

from __future__ import print_function
from sys import modules, path
from imp import find_module, load_module
from os import listdir
from os.path import dirname, realpath, split, splitext, join, isfile, \
    isabs, normpath
import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin
from sys import maxint
import wx.lib.rcsizer as rcs


class Addons:
    def __init__(self):
        "searches and reads addons descriptions files"
        pth1 = dirname(realpath(__file__))
        path.append(pth1)
        pth2 = APP_SETT.get_home()
        adds = []
        # find *.addon files
        for pth in (pth1, pth2):
            dir_lst = [i for i in listdir(pth) if i.endswith('.addon')]
            dir_lst.sort()
            appr = [join(pth, i) for i in dir_lst]
            # ensure that path is not directory or broken link
            adds += [i for i in appr if isfile(i)]
        descrs = []
        found_ids = set()
        for adf in adds:
            add_descr = {}
            # scanning *.addon file
            with open(adf) as fp:
                for line in fp:
                    ls = line.split('=', 1)
                    if len(ls) != 2:
                        continue
                    add_descr[ls[0]] = unicode(ls[1].strip(), 'utf-8')
            # validating the result of scanning
            is_valid = True
            for i in ('path', 'name', 'id'):
                if i not in add_descr:
                    is_valid = False
                    break
            if not is_valid:
                continue
            pth = add_descr['path']
            if not isabs(pth):
                pth = normpath(join(dirname(adf), pth))
                add_descr['path'] = pth
            if not isfile(pth):
                continue
            d_id = add_descr['id']
            if d_id.isdigit():
                d_id = int(d_id)
                add_descr['id'] = d_id
            if d_id in found_ids:
                continue
            add_descr['keys'] = set(add_descr.get('keys', '').split())
            found_ids.add(d_id)
            descrs.append(add_descr)
        self.descriptions = descrs

    def set_active(self, id_set=None):
        if id_set is None:
            id_set = APP_SETT.get("addons_ids", "set()")
            id_set = eval(id_set)
        for desc in self.descriptions:
            desc['isactive'] = desc['id'] in id_set

    def get_active(self, wgs=True):
        id_set = set()
        for desc in self.descriptions:
            if desc['isactive']:
                id_set.add(desc['id'])
        if wgs:
            APP_SETT.set("addons_ids", repr(id_set))
        return id_set

    def introduce(self, adds_dat):
        "modules loader"
        any_error = False
        for desc in self.descriptions:
            if desc['isactive'] and 'module' not in desc:
                pth, nam = split(splitext(desc['path'])[0])
                try:
                    fptr, pth, dsc = find_module(nam, [pth])
                    module = load_module(nam, fptr, pth, dsc)
                except ImportError:
                    desc['isactive'] = False
                    any_error = True
                    print('ImportError: %s' % nam)
                    continue
                if fptr:
                    fptr.close()
                mdata = dict(adds_dat[' base '])
                mdata['id'] = desc['id']
                adds_dat[desc['id']] = mdata
                if not hasattr(module, 'introduce') or \
                        module.introduce(mdata):
                    adds_dat.pop(desc['id'])
                    desc['isactive'] = False
                    any_error = True
                    print("Error: `%s' can't be introduced" % pth)
                    modules.pop(module.__name__)
                    continue
                desc['module'] = module
        if any_error:
            self.get_active()
        return any_error

    def terminate(self, adds_dat, all=False):
        "modules unloader"
        id_off = []
        for desc in self.descriptions:
            if 'module' in desc and (all or not desc['isactive']):
                module = desc.pop('module')
                mdata = adds_dat.pop(desc['id'])
                if hasattr(module, 'terminate'):
                    module.terminate(mdata)
                modules.pop(module.__name__)
                id_off.append(desc['id'])
        return id_off


def mod_from_desc(desc, adds_dat):
    "module loader"
    desc['isactive'] = True
    if 'module' not in desc:
        pth, nam = split(splitext(desc['path'])[0])
        try:
            fptr, pth, dsc = find_module(nam, [pth])
        except ImportError:
            desc['isactive'] = False
            print('ImportError: %s' % nam)
            return
        module = load_module(nam, fptr, pth, dsc)
        if fptr:
            fptr.close()
        mdata = dict(adds_dat[' base '])
        mdata['id'] = desc['id']
        adds_dat[desc['id']] = mdata
        if not hasattr(module, 'introduce') or \
                module.introduce(mdata):
            adds_dat.pop(desc['id'])
            desc['isactive'] = False
            print("Error: `%s' can't be introduced" % pth)
            modules.pop(module.__name__)
            return
        desc['module'] = module
        return module
    return desc['module']


# ########################   GUI Part   ###############################


class ChkListCtrl(wx.ListCtrl, CheckListCtrlMixin):
    def __init__(self, parent, size):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT |
                             wx.BORDER_NONE | wx.LC_SINGLE_SEL,
                             size=size)
        CheckListCtrlMixin.__init__(self)


class AddonsListCtrlPanel(wx.Panel):

    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS |
                          wx.SUNKEN_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.list = ChkListCtrl(self, size)
        sizer.Add(self.list, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.cfg = parent.cfg
        self.cfg.Bind(wx.EVT_BUTTON, self.on_configure)

    def PopulateList(self, descrs):
        self.descrs = descrs
        lstctr = self.list
        lstctr.Freeze()
        font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        _text = _("Use")
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        fc_wdth = int(dc.GetTextExtent(_text)[0] * 1.25)
        lstctr.InsertColumn(0, _text, width=fc_wdth,
                            format=wx.LIST_FORMAT_CENTRE)
        lwdth = lstctr.GetClientSizeTuple()[0]
        lstctr.InsertColumn(1, _("Title"), width=lwdth - fc_wdth)
        for data in descrs:
            index = lstctr.InsertStringItem(maxint, '')
            lstctr.SetStringItem(index, 1, data['name'])
            lstctr.CheckItem(index, data['isactive'])
        self.nitems = index + 1
        lstctr.Thaw()
        lstctr.Update()
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected, self.list)

    def on_item_selected(self, event):
        i = event.m_itemIndex
        self.cur_descr = self.descrs[i]
        self.cfg.Enable('configurable' in self.cur_descr['keys'] and
                        self.list.IsChecked(i))

    def set_addons_active_state(self):
        lst = self.list
        for i in xrange(len(self.descrs)):
            self.descrs[i]['isactive'] = lst.IsChecked(i)

    def on_configure(self, evt):
        curd = self.cur_descr
        parent = self.GetParent()
        add_dat = parent.GetParent().addons_data
        module = mod_from_desc(curd, add_dat)
        if module is None or not hasattr(module, 'Config'):
            if 'configurable' in curd['keys']:
                curd['keys'].remove('configurable')
            return
        cfg = module.Config(add_dat[curd['id']])
        dlg = DlgAddonConfig(parent, curd, cfg.get_visual)
        if dlg.ShowModal() == wx.ID_OK:
            cfg.configure()


class DlgAddonMgr(wx.Dialog):
    "Missing docstring"

    def __init__(self, parent, descrs):
        title = _("Addons")
        wx.Dialog.__init__(self, parent, -1, title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        cfg = wx.Button(self, -1, _("Configure..."))
        cfg.Enable(False)
        is_ok = wx.Button(self, wx.ID_OK)
        is_cancel = wx.Button(self, wx.ID_CANCEL)
        for i in (cfg, is_cancel, is_ok):
            hsizer.Add(i, 0, wx.ALIGN_CENTRE | wx.ALL | wx.EXPAND, 5)
        hsms = hsizer.GetMinSize()
        list_size = (max(350, hsms[0]), 420)
        self.cfg = cfg
        self.ulc = AddonsListCtrlPanel(self, list_size)
        self.ulc.PopulateList(descrs)
        sizer.Add(self.ulc, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(hsizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)


def run_addons_dialog(event=None):
    if event is None:
        window = None
    else:
        # this may be called from menu only
        window = event.GetEventObject().GetMenuBar().GetFrame()
    adds = APP_SETT.addons
    descrs = adds.descriptions
    DLG = DlgAddonMgr(window, descrs)
    if event is None:
        DLG.CenterOnScreen()
    if DLG.ShowModal() == wx.ID_OK and window:
        DLG.ulc.set_addons_active_state()
        adds.get_active()
        add_dat = window.addons_data
        adds.introduce(add_dat)
        a_menu = window.a_menu
        for i in adds.terminate(add_dat):
            a_menu.remove_add_id(i)
        a_menu.replay_actions()


class DlgAddonConfig(wx.Dialog):
    "Missing docstring"

    def __init__(self, parent, descr, get_vis):
        title = _(descr['name'])
        wx.Dialog.__init__(self, parent, -1, title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        vp = get_vis(self)
        sizer.Add(vp, 0, wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT |
                  wx.TOP, 5)
        hsizer = rcs.RowColSizer()
        is_ok = wx.Button(self, wx.ID_OK)
        is_cancel = wx.Button(self, wx.ID_CANCEL)
        hsizer.Add(is_cancel, 0, 0, 5, 0, 0)
        hsizer.AddGrowableCol(1)
        hsizer.Add(is_ok, 0, 0, 5, 0, 2)
        sizer.Add(hsizer, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)


if __name__ == '__main__':
    idict = {wx.ID_OK: "ID_OK", wx.ID_CANCEL: "ID_CANCEL"}
    APP = wx.PySimpleApp()
    from settings import prog_init
    prog_init()
    adds = APP_SETT.addons
    descrs = adds.descriptions
    adds.set_active(set([u'10', u'1', u'2', u'5', u'9', u'8']))
    DLG = DlgAddonMgr(None, descrs)
    DLG.CenterOnScreen()
    VAL = DLG.ShowModal()
    print(idict.get(VAL, VAL))
    if VAL == wx.ID_OK:
        DLG.ulc.set_addons_active_state()
        print(descrs)
        print(adds.get_active())
        adds.load_modules()
