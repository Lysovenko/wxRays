#!/usr/bin/env python
# -*- coding: utf-8 -*-
"This is some interesting educational program"
# wxRays (C) 2013 Serhii Lysovenko
#
# This program is free software; you can redistribute it and / or modify
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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.

# Used to guarantee to use at least Wx2.8
import wxversion
import os.path as osp
from sys import argv
wxversion.ensureMinimal('2.8')
import wx


class MainFrame(wx.Frame):
    'The Main Frame'
    def __init__(self):
        last_size = eval(APP_SETT.get("frame_size", "(550, 350)"))
        wx.Frame.__init__(self, None, - 1, PROG_NAME, size=last_size)
        from v_plot import Plot
        from v_menu import Active_menu
        from c_file import ascii_file_load
        self.data = {}
        adb = {'data': self.data, 'window': self}
        self.addons_data = {' base ': adb}
        self.a_menu = Active_menu(self)
        self.plot = Plot(self.a_menu)
        self.prev_dir = '.'
        adb.update({'plot': self.plot, 'menu': self.a_menu, 'loaders': []})
        APP_SETT.addons.introduce(self.addons_data)
        adb['loaders'].insert(0, (_('Commented dat files'), ('.dat',),
                                  ascii_file_load))
        self.a_menu.set_menu_bar()
        self.plot.mk_menuitems()
        self.canvas = self.plot.get_canvas(self)
        self.SetToolBar(self.plot.get_toolbar())
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.TOP | wx.LEFT | wx.EXPAND)
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_CLOSE(self, self.OnWindowClose)
        wx.EVT_SIZE(self, self.sizeHandler)
        self.a_menu.action_catch("on init")
        self.SetSizer(self.sizer)
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.SetStatusBar(self.statusBar)
        self.plot.set_statusbar(self.statusBar)

    def OnCreate(self):
        if len(argv) > 1:
            from v_dialogs import load_data_file
            load_data_file(self, argv[1:],
                           self.addons_data[' base ']['loaders'])

    def OnPaint(self, event):
        self.canvas.draw()
        event.Skip()

    def sizeHandler(self, event):
        self.canvas.SetInitialSize(self.GetClientSize())
        event.Skip()

    def OnWindowClose(self, event):
        APP_SETT.addons.terminate(self.addons_data, True)
        APP_SETT.set("frame_size", repr(self.GetSizeTuple()))
        self.Destroy()

    def OnDataFile(self, event):
        from v_dialogs import load_data_file
        load_data_file(self, None, self.addons_data[' base ']['loaders'])

    def AboutMe(self, evt):
        from v_dialogs import about_box
        about_box()


class TheSplashScreen(wx.SplashScreen):
    def __init__(self):
        splash_fname = osp.join(osp.dirname(__file__), u'splash.png')
        image = wx.Image(splash_fname, wx.BITMAP_TYPE_PNG)
        bmp = image.ConvertToBitmap()
        self.bmp = image.Resize((200, 200), (0, 0)).ConvertToBitmap()
        wx.SplashScreen.__init__(self, bmp, wx.SPLASH_CENTRE_ON_SCREEN |
                                 wx.SPLASH_TIMEOUT, 5000, None, - 1)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.fc = wx.FutureCall(2000, self.ShowMain)

    def OnClose(self, evt):
        # Make sure the default handler runs too so this window gets
        # destroyed
        evt.Skip()
        self.Hide()
        # if the timer is still running then go ahead and show the
        # main frame now
        if self.fc.IsRunning():
            self.fc.Stop()
            self.ShowMain()

    def ShowMain(self):
        import settings
        settings.prog_init()
        frame = MainFrame()
        frame.SetIcon(wx.IconFromBitmap(self.bmp))
        self.Hide()
        frame.OnCreate()
        frame.Show()


class App(wx.App):
    def OnInit(self):
        splash = TheSplashScreen()
        splash.Show()
        return True


def main():
    app = App(False)
    app.MainLoop()
    APP_SETT.save()
