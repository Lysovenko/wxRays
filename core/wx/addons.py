#!/usr/bin/env python
"This is Plugin Manager"
# wxRays (C) 2013-2017 Serhii Lysovenko
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
from ..addons import mod_from_desc
import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin
from sys import maxint
import wx.lib.rcsizer as rcs


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
