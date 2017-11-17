#!/usr/bin/env python
# -*- coding: utf-8 -*-
"Using Grig"
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
import wx.grid as Grid
import locale as loc
from v_dialogs import atof
from math import sin, asin, pi
_U_NAMES = [r"sin(\theta)", r"\theta", r"2\theta", r"\AA"]
_U_LABELS = [u"sin(\u03b8)", u"\u03b8", u"2\u03b8", u"\u212b"]


class ReflexesGrid(Grid.Grid):
    "Creates a grid with reflexes positions"
    def __init__(self, parent):
        Grid.Grid.__init__(self, parent, -1)
        self.CreateGrid(25, 4)
        self._rows = 25
        self._cols = 4
        self.SetColLabelValue(0, _("Location"))
        self.SetColLabelValue(1, _("Intensity"))
        self.SetColLabelValue(2, _("Comment"))
        self.SetColLabelValue(3, _("Frozen"))
        attr = Grid.GridCellAttr()
        attrb = Grid.GridCellAttr()
        attr.SetEditor(Grid.GridCellFloatEditor())
        attrb.SetEditor(Grid.GridCellBoolEditor())
        attrb.SetRenderer(Grid.GridCellBoolRenderer())
        self.SetColAttr(0, attr)
        self.SetColAttr(1, attr)
        self.SetColSize(2, self.GetColSize(2) * 4)
        self.SetColAttr(3, attrb)
        self.Bind(Grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClicked)
        self.Bind(Grid.EVT_GRID_CELL_CHANGE, self.OnCellChange)
        wx.EVT_KEY_DOWN(self, self.on_key)

    def make_idata(self, refpos):
        if refpos is None:
            self.idata = [[None] * 4 for i in xrange(25)]
            return
        self.idata = [list(i) for i in refpos]
        idl = len(self.idata)
        if idl < 25:
            self.idata += [[None] * 4 for i in xrange(25 - idl)]

    def export_refpos(self):
        return [tuple(i) for i in self.idata if i[0] is not None and i[0] > 0.]

    def change_units(self, units, wavel):
        if units == r'sin(\theta)':
            self.loc_put = self.loc_get = lambda x: x
        if units == r'\theta':
            self.loc_put = lambda x, m=180. / pi: asin(x) * m
            self.loc_get = lambda x, m=pi / 180.: sin(x * m)
        if units == r'2\theta':
            self.loc_put = lambda x, m=360. / pi: m * asin(x)
            self.loc_get = lambda x, m=pi / 360.: sin(x * m)
        if units == r'\AA' and wavel is not None:
            self.loc_put = self.loc_get = lambda x, w=wavel / 2.: w / x
        self.show_idata()

    def show_idata(self):
        cur = self._rows
        if len(self.idata) > cur:
            self._rows = len(self.idata)
            self.GetTable().InsertRows(0, self._rows - cur)
        self.Reset()
        conv = self.loc_put
        for p, (l, i, c, f) in enumerate(self.idata):
            if l is None:
                self.SetCellValue(p, 0, "")
            else:
                self.SetCellValue(p, 0, loc.str(conv(l)))
            if i is None:
                self.SetCellValue(p, 1, "")
            else:
                self.SetCellValue(p, 1, loc.str(i))
            if c is None:
                self.SetCellValue(p, 2, "")
            else:
                self.SetCellValue(p, 2, c)
            if f:
                self.SetCellValue(p, 3, '1')
            else:
                self.SetCellValue(p, 3, '')

    def OnLabelRightClicked(self, evt):
        # Did we click on a row or a column?
        row, col = evt.GetRow(), evt.GetCol()
        if row >= 0:
            self.rowPopup(row, evt)

    def rowPopup(self, row, evt):
        "(row, evt) -> display a popup menu when a row label is right clicked"
        appendID = wx.NewId()
        deleteID = wx.NewId()
        x = self.GetRowSize(row) / 2
        if not self.GetSelectedRows():
            self.SelectRow(row)
        menu = wx.Menu()
        xo, yo = evt.GetPosition()
        menu.Append(appendID, "Append Row")
        menu.Append(deleteID, "Delete Row(s)")

        def append(event, self=self, row=row):
            self.GetTable().InsertRows(row)
            self.idata.insert(row, [None, None, None, False])
            self._rows += 1
            self.Reset()

        def delete(event, self=self, row=row):
            rows = self.GetSelectedRows()
            deleted = 0
            prev = rows[0]
            ndel = 1
            sdel = prev
            for i in rows[1:]:
                if i - prev == 1:
                    ndel += 1
                else:
                    self.GetTable().DeleteRows(sdel - deleted, ndel)
                    self._rows -= ndel
                    deleted += ndel
                    ndel = 1
                    sdel = i
                prev = i
            self.GetTable().DeleteRows(sdel - deleted, ndel)
            self._rows -= ndel
            idt = self.idata
            for i, j in enumerate(rows):
                idt.pop(j - i)
            self.Reset()

        self.Bind(wx.EVT_MENU, append, id=appendID)
        self.Bind(wx.EVT_MENU, delete, id=deleteID)
        self.PopupMenu(menu)
        menu.Destroy()
        return

    def Reset(self):
        "Reset Grid"
        self.BeginBatch()
        current = self._rows
        new = self.GetNumberRows()
        delmsg = Grid.GRIDTABLE_NOTIFY_ROWS_DELETED
        addmsg = Grid.GRIDTABLE_NOTIFY_ROWS_APPENDED
        tab = self.GetTable()
        if new < current:
            msg = Grid.GridTableMessage(tab, delmsg, new, current - new)
            self.ProcessTableMessage(msg)
        elif new > current:
            msg = Grid.GridTableMessage(tab, addmsg, new - current)
            self.ProcessTableMessage(msg)
        self.EndBatch()
        self.AdjustScrollbars()
        self.ForceRefresh()

    def OnCellChange(self, evt):
        r = evt.GetRow()
        c = evt.GetCol()
        value = self.GetCellValue(r, c)
        try:
            if c == 0:
                self.idata[r][0] = self.loc_get(atof(value))
            elif c == 1:
                self.idata[r][1] = atof(value)
            elif c == 2:
                self.idata[r][2] = value
            else:
                self.idata[r][3] = value == '1'
        except (ValueError, ZeroDivisionError):
            self.idata[r][c] = None

    def on_key(self, event):
        k_code = event.GetKeyCode()
        ctrl = event.ControlDown()
        if k_code == wx.WXK_DELETE:
            idata = self.idata
            tl = self.GetSelectionBlockTopLeft()
            if tl:
                tlr, tlc = tl[0]
                brr, brc = self.GetSelectionBlockBottomRight()[0]
                for r in xrange(tlr, brr + 1):
                    for c in xrange(tlc, brc + 1):
                        self.SetCellValue(r, c, '')
                        idata[r][c] = None
            else:
                r = self.GetGridCursorRow()
                c = self.GetGridCursorCol()
                self.SetCellValue(r, c, '')
                idata[r][c] = None
        elif k_code == 67 and ctrl:
            # Ctrl+C
            self.copy()
        elif k_code == 86 and ctrl:
            # Ctrl+V
            self.paste()
        elif k_code == 88 and ctrl:
            # Ctrl+X
            self.clear()
        else:
            event.Skip()

    def copy(self):
        "Copy method"
        # Number of rows and cols
        tl = self.GetSelectionBlockTopLeft()
        if tl:
            tlr, tlc = tl[0]
            brr, brc = self.GetSelectionBlockBottomRight()[0]
        # data variable contain text that must be set in the clipboard
            data = ''
            outab = [[self.GetCellValue(r, c) for c in xrange(tlc, brc + 1)]
                     for r in xrange(tlr, brr + 1)]
            data = u"\n".join([u"\t".join(i) for i in outab])
        else:
            r = self.GetGridCursorRow()
            c = self.GetGridCursorCol()
            data = self.GetCellValue(r, c)
        clipboard = wx.TextDataObject()
        # Set data object value
        clipboard.SetText(data)
        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

    def paste(self):
        rs = self.GetGridCursorRow()
        cs = self.GetGridCursorCol()
        clipboard = wx.TextDataObject()
        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(clipboard)
            wx.TheClipboard.Close()
        else:
            return
        text = clipboard.GetText()
        idat = self.idata
        for tpos, line in enumerate(text.splitlines(), rs):
            if len(idat) == tpos:
                idat.append([None, None, None])
            for rpos, cval in enumerate(line.split("\t"), cs):
                if rpos >= 3:
                    break
                try:
                    if rpos == 0:
                        idat[tpos][0] = self.loc_get(atof(cval))
                    elif rpos == 1:
                        idat[tpos][1] = atof(cval)
                    else:
                        idat[tpos][2] = cval
                except (ValueError, ZeroDivisionError):
                    idat[tpos][rpos] = None
        self.show_idata()

    def clear(self):
        self.idata = [[None, None, None, False] for i in range(25)]
        self.show_idata()


class RefLocFrame(wx.Frame):
    def __init__(self, internal, caller=None):
        parent = internal["window"]
        wx.Frame.__init__(self, parent, -1, _("Predefined reflexes"),
                          size=eval(internal["refloc_sz"]))
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        if "Exp. data" in internal["data"]:
            ed = internal["data"]["Exp. data"]
            if ed.lambda1 is not None:
                self.wavel = ed.lambda1
            else:
                self.wavel = ed.wavel
        else:
            self.wavel = None
        self.internal = internal
        self.caller = caller
        self.grid = ReflexesGrid(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Location units:"))
        hbox.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.units = wx.Choice(self, -1, choices=_U_LABELS)
        hbox.Add(self.units, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(hbox, 0, wx.EXPAND, 5)
        sizer.Add(self.grid, 1, wx.EXPAND)
        self.SetSizer(sizer)
        wx.EVT_CLOSE(self, self.OnWindowClose)
        self.Bind(wx.EVT_CHOICE, self.on_ch_units, self.units)
        self.grid.make_idata(caller.get(False))
        self.grid.change_units(_U_NAMES[0], self.wavel)
        self.Show()

    def set_cells(self, edata):
        self.grid.make_idata(edata)
        curs = self.units.GetCurrentSelection()
        self.grid.change_units(_U_NAMES[curs], self.wavel)

    def get_refpos(self):
        return self.grid.export_refpos()

    def OnWindowClose(self, event):
        self.internal["refloc_sz"] = repr(self.GetSizeTuple())
        self.caller.del_frame()
        self.caller.set(self.grid.export_refpos())
        self.Destroy()

    def on_ch_units(self, event):
        self.grid.change_units(_U_NAMES[event.GetSelection()], self.wavel)
