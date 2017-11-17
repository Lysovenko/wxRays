# -*- coding: utf-8 -*-
"menu generator"
# wxRays (C) 2013 Serhii Lysovenko
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or (at
# your option) any later version.
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
from __future__ import print_function, absolute_import, unicode_literals
import wx


class Active_menu:
    def __init__(self, frame):
        self.frame = frame
        frame.SetMenuBar(wx.MenuBar())
        self.menus = {"file": wx.Menu(), "data": wx.Menu(),
                      "plot": wx.Menu(), "help": wx.Menu(),
                      "tools": wx.Menu()}
        self.menu_items = []
        self.act_history = []
        self.act_catchers = []

    def set_menu_bar(self):
        from .addons import run_addons_dialog
        from .datmod import VDM_menu
        frame = self.frame
        menubar = frame.GetMenuBar()
        data = frame.addons_data[' base ']
        _mitems = [(None, _("&File"), "file", None, None),
                   ({}, _("&Open data file(s)...") + "\tCtrl+O",
                    frame.OnDataFile, wx.ART_FILE_OPEN, 0),
                   (None, None, None, None, None),
                   ({}, _("&Quit") + "\tCtrl+Q", frame.OnWindowClose,
                    wx.ART_QUIT, None),
                   (None, _("&Data"), "data", None, None),
                   ({"on init": False, 'on plot': set([_("Intensity curve")])},
                    _("Crop the intensity curve"),
                    VDM_menu(data, 'crop_data'), None, 0),
                   ({"on init": False, 'on plot': set([_("Intensity curve")])},
                    _("Shift the intensity curve..."),
                    VDM_menu(data, 'shift_data'), None, 1),
                   (None, None, None, None, 2),
                   (None, _("&Plot"), "plot", None, None),
                   (None, _("&Tools"), "tools", None, None),
                   ({}, _("Addons..."), run_addons_dialog, None, 0),
                   (None, _("Help"), "help", None, None),
                   ({}, _("About..."), frame.AboutMe, wx.ART_HELP, None)]
        evt = wx.EVT_MENU
        for act, name, callb, bmp, pos in _mitems:
            if act is None:
                if name is None:
                    if pos is None:
                        menu.AppendSeparator()
                    else:
                        menu.InsertSeparator(pos)
                else:
                    menu = self.menus[callb]
                    menubar.Append(menu, name)
            else:
                ami = Menu_item(act)
                self.menu_items.append(ami)
                qmi = ami.wx_menu_item(menu, name)
                if bmp is not None:
                    qmi.SetBitmap(wx.ArtProvider.GetBitmap(bmp))
                if pos is None:
                    menu.AppendItem(qmi)
                else:
                    menu.InsertItem(pos, qmi)
                frame.Bind(evt, callb, id=ami.id)

    def add_catcher(self, catcher):
        if catcher not in self.act_catchers:
            self.act_catchers.append(catcher)

    def action_catch(self, action, condition=None):
        "action catcher"
        hist = self.act_history
        if hist and hist[-1] == action:
            return
        if action in hist:
            if action.startswith('!'):
                hist.remove(action)
            else:
                del(hist[hist.index(action):])
        if condition is None:
            hist.append(action)
        for i in self.menu_items:
            i.action_catch(action, condition)
        for i in self.act_catchers:
            i(action, condition)

    def replay_actions(self):
        "replay menu actions"
        if self.act_history:
            for i in self.act_history:
                for j in self.menu_items:
                    j.action_catch(i, None)

    def add_item(self, m_nam, act, name, callb, bmp=None, add_id=None,
                 kind=wx.ITEM_NORMAL, s_nam=None):
        menu = self.menus[m_nam]
        if name is None:
            menu.AppendSeparator()
            return
        if s_nam:
            smenu = wx.Menu()
            self.menus[s_nam] = smenu
        else:
            smenu = None
        ami = Menu_item(act)
        ami.addons_id = add_id
        self.menu_items.append(ami)
        qmi = ami.wx_menu_item(menu, name, kind=kind, subMenu=smenu)
        if bmp is not None:
            qmi.SetBitmap(wx.ArtProvider.GetBitmap(bmp))
        if m_nam == "file" and menu.MenuItemCount > 2:
            menu.InsertItem(menu.MenuItemCount - 2, qmi)
        else:
            menu.AppendItem(qmi)
        if callb:
            self.frame.Bind(wx.EVT_MENU, callb, qmi)
        return ami.id

    def remove_add_id(self, add_id):
        mitems = self.menu_items
        frame = self.frame
        evt = wx.EVT_MENU
        i = 0
        dnd = []
        while i < len(mitems):
            if mitems[i].is_rm_add_id(add_id):
                ami = mitems.pop(i)
                if ami.has_sub:
                    dnd.append(ami)
                else:
                    frame.Unbind(evt, id=ami.id)
                    ami.destroy()
            else:
                i += 1
        menus = self.menus
        for ami in reversed(dnd):
            sm = ami.menu_item.GetSubMenu()
            for nmi in menus:
                if menus[nmi] is sm:
                    menus.pop(nmi)
                    break
            ami.destroy()

    def remove_id(self, id):
        mitems = self.menu_items
        for ami in mitems:
            if ami.id == id:
                self.frame.Unbind(wx.EVT_MENU, id=id)
                ami.destroy()
                mitems.remove(ami)
                break


class Menu_item:
    def __init__(self, actions={}):
        self.id = wx.NewId()
        while 2000 <= self.id < 2100:
            self.id = wx.NewId()
        self.actions = actions
        self.addons_id = None

    def wx_menu_item(self, parentMenu=None, text="", help="",
                     kind=wx.ITEM_NORMAL, subMenu=None):
        self.menu_item = wx.MenuItem(parentMenu, self.id, text, help, kind,
                                     subMenu)
        self.has_sub = subMenu is not None
        return self.menu_item

    def action_catch(self, action, condition):
        if action in self.actions:
            enable = self.actions[action]
            if type(enable) == bool:
                self.menu_item.Enable(enable)
            else:
                self.menu_item.Enable(condition in enable)

    def is_rm_add_id(self, add_id):
        if self.addons_id and self.addons_id == add_id:
            return True
        return False

    def destroy(self):
        self.menu_item.GetMenu().DestroyId(self.id)
