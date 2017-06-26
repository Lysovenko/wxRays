#!/usr/bin/env python
"db interface"
# wxRays (C) 2013-2016 Serhii Lysovenko
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
import wx.html
from wx.lib.mixins.listctrl import ListRowHighlighter
import sys
from PDDB import Database, formula_markup, switch_number
from marshal import dump, load
import os.path as osp
import locale
_DEFAULTS = {"main_file": "", "incl_del": 0, "win_size":  "(-1, -1)"}


def introduce(data):
    "Addons Entry point"
    global INTERNAL
    INTERNAL = data
    data["menu"].add_item("tools", {}, _("PD DB..."),
                          Menu_callback(data), wx.ART_CDROM, data["id"])
    APP_SETT.declare_section("PDDB")
    iget = APP_SETT.get
    for i in _DEFAULTS:
        data[i] = iget(i, _DEFAULTS[i], "PDDB")


def terminate(data):
    "Addon unloader"
    crd_lst = data.get("CrdLst")
    if crd_lst:
        crd_lst.on_window_close()
    iset = APP_SETT.set
    for i in _DEFAULTS:
        iset(i, data[i], "PDDB")
    sys.modules.pop("PDDB")


class Menu_callback:
    def __init__(self, data):
        self.data = data

    def __call__(self, evt):
        dat = self.data
        if not dat.get("CrdLst"):
            database = Database(dat["main_file"])
            if database:
                dat["CrdLst"] = DBCardsList(dat, database)
        else:
            dat["CrdLst"].Raise()


class Config:
    def __init__(self, data):
        self.data = data

    def get_visual(self, parent):
        import wx.lib.filebrowsebutton as filebrowse
        self.fbb = filebrowse.FileBrowseButton(
            parent, labelText=_("DB file:"),
            buttonText=_("Open"), dialogTitle=_("Open the database file"),
            fileMask=_("PD database|*.db"),
            fileMode=wx.OPEN, size=wx.Size(300, -1),
            initialValue=self.data["main_file"])
        return self.fbb

    def configure(self):
        fnam = self.fbb.GetValue()
        self.data["main_file"] = fnam


class RHListCtrl(wx.ListCtrl, ListRowHighlighter):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ListRowHighlighter.__init__(self)
        self.SetHighlightColor("light gray")


class DBCardsList:
    def __init__(self, internal, database):
        self.internal = internal
        parent = internal["window"]
        self.__db = database
        self.__parent = parent
        self.__plot = internal["plot"]
        self.__data = internal["data"]
        self.__mname = _("PDDB Pattern")
        self.__frame = wx.Frame(parent, -1, _("DB Cards"))
        if parent is not None:
            self.__frame.SetIcon(parent.GetIcon())
        self.__htmlist = []
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.filter = wx.SearchCtrl(
            self.__frame, style=wx.TE_PROCESS_ENTER,
            size=(self.__frame.GetCharWidth() * 20, -1))
        self.filter.SetFocus()
        searchMenu = wx.Menu()
        self.incl_del = searchMenu.AppendCheckItem(-1, _("Include deleted"))
        self.filter.SetMenu(searchMenu)
        self.incl_del.Check(bool(INTERNAL["incl_del"]))
        self.filter.Bind(wx.EVT_TEXT_ENTER, self.filter_elments)
        sizer.Add(self.filter, 0, wx.EXPAND | wx.ALL, 5)
        self.__list = RHListCtrl(self.__frame)
        sizer.Add(self.__list, -1, flag=wx.EXPAND)
        self.__frame.SetSizer(sizer)
        self.__list.InsertColumn(0, _("Number"))
        self.__list.InsertColumn(1, _("Name"))
        self.__list.InsertColumn(2, _("Formula"))
        self.__list.InsertColumn(3, _("Quality"))
        self.__frame.SetSize(eval(internal["win_size"]))
        self.__frame.Show(True)
        self.__frame.Bind(wx.EVT_CLOSE, self.on_window_close)
        self.__list.Bind(wx.EVT_LIST_KEY_DOWN, self.list_event)
        self.__list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_event)
        self.__list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.list_event)
        self.__list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.popup_menu)
        self.__popup = popup = wx.Menu()
        self.__popact = acts = {}
        self.__popitm = itms = {}
        for action, name in (
                ("Info", _("Card's information")),
                ("Delete", _("Delete")), ("Clear", _("Clear")),
                ("prepos", _("Preserve positions"))):
            xid = wx.NewId()
            acts[xid] = action
            itms[action] = popup.Append(xid, name)
        self.__frame.Bind(wx.EVT_MENU, self.popup_selected)
        self.cards = set()
        self.__alive = True
        self.html_mdi = None

    def __nonzero__(self):
        return self.__alive

    def plot_pattern(self, unum):
        "plot the current pattern"
        cid = switch_number(unum)
        if "Exp. data" in self.__data:
            ed = self.__data["Exp. data"]
            chromos = []
            wavels = []
            if ed.wavel is not None:
                wavels.append(ed.wavel)
            if ed.lambda1 is not None:
                chromos.append((ed.lambda1, 1.))
            if ed.lambda2 is not None:
                chromos.append((ed.lambda2, ed.I2))
            if ed.lambda3 is not None:
                chromos.append((ed.lambda3, ed.I3))
                wavels.append(ed.lambda3)
        else:
            chromos = None
        plt = self.__plot
        pln = plt.get_cur_key()
        mpln = self.__mname
        units = plt.cur_xunits
        if pln:
            cd = plt.get_cur_data()
            if "wavelength" in cd.tech_info and not chromos:
                chromos = [(cd.tech_info["wavelength"], 1.)]
                wavels = [cd.tech_info["wavelength"]]
            if "wavelength" in cd.tech_info:
                wavel = cd.tech_info["wavelength"]
        if pln and pln != mpln and units in (
                "A", "A^{-1}", "sin(\\theta)",
                "2\\theta", "\\theta") and not cd.ax2:
            colors = ("red", "orange", "green")
            cd = cd.clone()
            for clr, (wavel, intens) in enumerate(chromos):
                x, y = self.__db.get_di(cid, units, wavel)
                y *= intens
                cd.append((x, y, 2, colors[clr], "pulse"))
            cd.set_info(self.__db.wiki_di(cid, units, wavels, cd))
            plt.set_data(mpln, cd)
            plt.plot_dataset(mpln)
            return
        if mpln in plt:
            cd = plt.get_data(mpln)
            if "wavelength" in cd.tech_info:
                wavel = cd.tech_info["wavelength"]
            units = cd.get_units()
            last = []
            if not chromos:
                chromos = [(0., 1.)]
                wavels = [0]
            for wavel, intens in chromos:
                x, y = self.__db.get_di(cid, units, wavel)
                y *= intens
                last.append((x, y))
            cd.replace_last(last)
            cd.set_info(self.__db.wiki_di(cid, units, wavels, cd))
            plt.plot_dataset(mpln)
            return
        x, y = self.__db.get_di(cid, "A^{-1}", 0.)
        plt.set_data(mpln, [(x, y, 1, None, "pulse")], r"$\AA^{-1}$",
                     "I, %", "A^{-1}")
        plt.get_data(mpln).set_info(
            self.__db.wiki_di(cid, "A^{-1}", [0]))
        plt.plot_dataset(mpln)

    def on_window_close(self, evt=None):
        "closing and making self False"
        if self.html_mdi:
            self.html_mdi.on_window_close(evt)
            del self.__htmlist
        self.internal["win_size"] = repr(self.__frame.GetSizeTuple())
        self.internal["incl_del"] = int(self.incl_del.IsChecked())
        self.__frame.Destroy()
        self.__alive = False
        self.__db.close()
        del self.cards

    def Raise(self):
        self.__frame.Raise()

    def filter_elments(self, evt=None):
        if "GetKeyCode" in dir(evt) and \
                evt.GetKeyCode() not in [0, wx.WXK_RETURN]:
            evt.Skip()
            return
        text = self.filter.GetValue()
        incl_del = self.incl_del.IsChecked()
        self.filter.SetValue("")
        try:
            rows = self.__db.select_cards(text)
        except ValueError:
            wx.MessageBox(_("Wrong query"), _("Error"))
            rows = ()
        for cid, name, formula, qual in rows:
            unum = switch_number(cid)
            # maybe it should be virtual list
            # but now max number of items will be limited
            max_items = 300
            if cid in self.cards:
                continue
            self.cards.add(cid)
            index = self.__list.InsertStringItem(sys.maxint, unum)
            self.__list.SetStringItem(index, 1, name)
            self.__list.SetStringItem(
                index, 2, formula.replace("!", u"\u00d7"))
            qual = qual[1] + (qual[0] == 'D' and u"\u22a0" or u"\u22a1")
            self.__list.SetStringItem(index, 3, qual)
            if index > max_items:
                break
        self.__list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.__list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.__list.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.__list.RefreshRows()

    def popup_menu(self, event):
        "popup local menu"
        internal = self.internal
        if "User refl" in internal["data"]:
            self.__popitm["prepos"].Enable(True)
        else:
            self.__popitm["prepos"].Enable(False)
        index = event.GetIndex()
        unum = event.GetText()
        pos = event.GetPosition()
        self.__pop_pos = index, unum
        self.__frame.PopupMenu(self.__popup, pos)

    def popup_selected(self, event):
        action = self.__popact[event.GetId()]
        index, unum = self.__pop_pos
        if action is "Delete":
            delp = self.__list.GetFirstSelected()
            dlist = []
            while delp >= 0:
                dlist.append(delp)
                delp = self.__list.GetNextSelected(delp)
            for i, j in enumerate(dlist):
                p = j - i
                cid = switch_number(self.__list.GetItemText(p))
                self.__list.DeleteItem(p)
                self.cards.discard(unum)
            self.__list.RefreshRows()
        if action is "Info":
            self.info_window(unum)
        if action is "Clear":
            self.__list.DeleteAllItems()
            self.cards.clear()
        if action is "prepos":
            self.predefine_reflexes(unum)

    def list_event(self, event):
        k_code = event.GetKeyCode()
        index = event.GetIndex()
        unum = event.GetText()
        cid = switch_number(unum)
        if k_code == wx.WXK_DELETE:
            self.__list.DeleteItem(index)
            self.cards.discard(cid)
            self.__list.RefreshRows()
        elif k_code == ord("i") or k_code == ord("I"):
            self.info_window(unum)
        elif k_code == ord("X"):
            self.__list.DeleteAllItems()
            self.cards.clear()
        elif k_code == wx.WXK_RETURN or k_code == 0:
            self.plot_pattern(unum)
        event.Skip()

    def info_window(self, unum):
        if not unum:
            return
        cid = switch_number(unum)
        popnew = True
        for htmw in self.__htmlist:
            if htmw.popup(cid):
                popnew = False
                break
        if popnew:
            if not self.html_mdi:
                self.html_mdi = HTML_MDI(self.__frame)
            html = HTML_CardInfo(
                self.html_mdi, self.__db, cid, self.__htmlist)
            self.__htmlist.append(html)

    def predefine_reflexes(self, unum):
        if not unum:
            return
        cid = switch_number(unum)
        if "Exp. data" in self.__data:
            ed = self.__data["Exp. data"]
            if ed.lambda1 is not None:
                wavel = ed.lambda1
            else:
                wavel = ed.wavel
        else:
            return
        wavel /= 2.
        result = []
        for reflex in self.__db.reflexes(cid, True):
            p = wavel / reflex[0]
            if p > 1.:
                continue
            i = float(reflex[1])
            if reflex[2] is None:
                c = unum
            else:
                c = "%s (%d %d %d)" % ((unum,) + reflex[2:])
            result.append((p, i, c))
        self.internal["data"]["User refl"].append(result)


class HTML_MDI(wx.MDIParentFrame):
    def __init__(self, parent):
        wx.MDIParentFrame.__init__(self, parent, -1, _("Cards info"))
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        self.alive = True
        self.Bind(wx.EVT_CLOSE, self.on_window_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char)
        self.Show()

    def __nonzero__(self):
        return self.alive

    def on_window_close(self, evt):
        "closing and making self False"
        self.Destroy()
        self.alive = False

    def on_char(self, event):
        if event.Modifiers == wx.MOD_CONTROL and event.KeyCode in (3, ord('C')):
            self.GetActiveChild().html2clipboard()
            return
        if event.Modifiers == wx.MOD_CONTROL and event.KeyCode == ord('T'):
            self.GetActiveChild().tabular2clipboard()
            return
        if event.KeyCode == wx.WXK_ESCAPE:
            self.GetActiveChild().Destroy()
            return
        event.Skip()


class HTML_CardInfo(wx.MDIChildFrame):
    def __init__(self, parent, db, cid, htmlist):
        self.htmlist = htmlist
        self.__db = db
        self.cid = cid
        self.parent = parent
        wx.MDIChildFrame.__init__(self, parent, -1, switch_number(self.cid))
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        self.__ht = self.mkhtext()
        html.SetPage(self.__ht)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_window_destroy)
        self.parent.Raise()
        self.Show()

    def html2clipboard(self):
        clipdata = wx.TextDataObject()
        clipdata.SetText(self.__ht)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

    def on_window_destroy(self, evt=None):
        self.htmlist.remove(self)

    def popup(self, cid):
        if self.cid == cid:
            self.parent.Raise()
            self.Activate()
            return True
        return False

    def mkhtext(self):
        db = self.__db
        cid = self.cid
        qual = db.quality(cid)
        qual = qual[1] + _(" (Deleted)") if qual[0] == "D" else qual[1]
        res = (_("""
<table>
<tr><td>Number:</td><td>%(num)s</td></tr>
<tr><td>Name:</td><td>%(nam)s</td></tr>
<tr><td>Formula:</td><td>%(fml)s</td></tr>
<tr><td>Quality:</td><td>%(qlt)s</td></tr>
""") %
               {"num": switch_number(cid), "nam": db.name(cid),
                "fml": db.formula_markup(cid), "qlt": qual})
        cell = db.cell_params(cid)
        if cell:
            pnr = ["a", "b", "c", u"\u03b1", u"\u03b2", u"\u03b3"]
            res += "<tr><td>%s</td><td>" % _("Cell parameters:")
            ppr = []
            for p, v in cell:
                ppr.append("%s=%s" % (pnr[p], locale.format("%g", v)))
            res += "; ".join(ppr) + "</td></tr>\n"
        spc_grp = db.spacegroup(cid)
        if spc_grp:
            res += "<tr><td>%s</td><td>%s</td></tr>\n" % \
                (_("Space group:"), spc_grp)
        res += "</table>\n"
        rtbl = "<br>\n<br>\n<table border=1>\n"
        rtblr = "<tr>"
        rcels = 0
        for reflex in db.reflexes(cid, True):
            if reflex[2] is None:
                rtblr += "<td><pre> %s %3d </pre></td>" % \
                    ((locale.format("%.5f", reflex[0]),) + reflex[1:2])
            else:
                rtblr += "<td><pre> %s %3d  %4d%4d%4d </pre></td>" % \
                    ((locale.format("%.5f", reflex[0]),) + reflex[1:])
            rcels += 1
            if rcels == 3:
                rtbl += rtblr + "</tr>\n"
                rtblr = "<tr>"
                rcels = 0
        if rcels:
            for reflex in xrange(rcels, 3):
                rtblr += "<td></td>"
            rtbl += rtblr + "</tr>\n"
        res += rtbl + "</table>\n"
        comment = db.comment(cid)
        if comment:
            res += _("<h5>Comment</h5>")
            for cod, val in comment:
                if cod == "CL":
                    res += _("Color: ")
                res += val + "<br>\n"
        res += _("<h5>Bibliography</h5>\n")
        res += "<ul>\n"
        for source, vol, page, year, authors in db.citations(cid):
            lit = "<li>"
            if authors:
                lit += "%s // " % authors
            if source:
                lit += source
            if vol:
                lit += ", <b>%s</b>" % vol
            if page:
                lit += ", P. %s" % page
            if year:
                lit += " (%d)" % year
            res += lit + "</li>\n"
        res += "</ul>\n"
        return "".join(["<html><body>", res, "</body></html>"])

    def tabular2clipboard(self):
        result = ""
        for reflex in sorted(self.__db.reflexes(self.cid, True), reverse=True):
            if reflex[2] is None:
                result += "%s\t%d\n" % \
                    ((locale.format("%.5f", reflex[0]),) + reflex[1:2])
            else:
                result += "%s\t%d\t%d %d %d\n" % \
                    ((locale.format("%.5f", reflex[0]),) + reflex[1:])
        clipdata = wx.TextDataObject()
        clipdata.SetText(result)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
