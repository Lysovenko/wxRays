#!/usr/bin/env python
# -*- coding: utf-8 -*-
"db interface"
# wxRays (C) 2013-2014 Serhii Lysovenko
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
from NIST import NIST_Card, ElFilter, string_card
from marshal import dump, load
import os.path as osp
import locale
_DEFAULTS = {"main_file": "", "incl_del": 0, "win_size":  "(-1, -1)"}


def introduce(data):
    "Addons Entry point"
    global INTERNAL
    INTERNAL = data
    data['menu'].add_item("tools", {}, _("NIST database..."),
                          Menu_callback(data), wx.ART_CDROM, data['id'])
    APP_SETT.declare_section('NISTDB')
    iget = APP_SETT.get
    for i in _DEFAULTS:
        data[i] = iget(i, _DEFAULTS[i], 'NISTDB')


def terminate(data):
    "Addon unloader"
    crd_lst = data.get('CrdLst')
    if crd_lst:
        crd_lst.on_window_close()
    iset = APP_SETT.set
    for i in _DEFAULTS:
        iset(i, data[i], 'NISTDB')
    sys.modules.pop("NIST")


class Menu_callback:
    def __init__(self, data):
        self.data = data

    def __call__(self, evt):
        dat = self.data
        if not dat.get('CrdLst'):
            index = db_load_index()
            if index is not None:
                dat['CrdLst'] = DBCardsList(dat, index)
        else:
            dat['CrdLst'].Raise()


class Config:
    def __init__(self, data):
        self.data = data

    def get_visual(self, parent):
        import wx.lib.filebrowsebutton as filebrowse
        self.fbb = filebrowse.FileBrowseButton(
            parent, labelText=_('DB file:'),
            buttonText=_('Open'), dialogTitle=_("Open main database file"),
            fileMask=_("NIST*AIDS-83 database format|pdf2.dat"),
            fileMode=wx.OPEN, size=wx.Size(300, -1),
            initialValue=self.data["main_file"])
        return self.fbb

    def configure(self):
        fnam = self.fbb.GetValue()
        indnam = APP_SETT.get_home("DB_el.idx")
        indnam_d = APP_SETT.get_home("DB_el_d.idx")
        try:
            indexate_with_progress(fnam, indnam, indnam_d)
        except (ValueError, IndexError):
            wx.MessageBox(_("Wrong database file"), _("Error!"),
                          wx.OK | wx.ICON_ERROR | wx.CENTER)
            return False
        self.data["main_file"] = fnam


def get_codens_dict():
    codesnam = APP_SETT.get_home("codens.dmp")
    try:
        fobj = open(codesnam, "rb")
    except IOError:
        codest = osp.dirname(INTERNAL["main_file"])
        codest = osp.join(codest, "codens.dat")
        res = {}
        if not osp.isfile(codest):
            return res
        with open(codest, "rb") as fobj:
            buf = fobj.read(80)
            while buf:
                res[buf[:6]] = buf[7:].strip()
                buf = fobj.read(80)
        with open(codesnam, "wb") as fobj:
            dump(res, fobj)
        return res
    with fobj:
        return load(fobj)


def db_load_index():
    indnam = APP_SETT.get_home("DB_el.idx")
    indnam_d = APP_SETT.get_home("DB_el_d.idx")
    try:
        fobj = open(indnam, "rb")
        fobj_d = open(indnam_d, "rb")
    except IOError:
        if db_make_index(indnam, indnam_d):
            fobj = open(indnam, "rb")
            fobj_d = open(indnam_d, "rb")
        else:
            return None
    obj = load(fobj)
    obj_d = load(fobj_d)
    fobj.close()
    fobj_d.close()
    return obj, obj_d


def db_make_index(indnam, indnam_d):
    wild = _("NIST*AIDS-83 database format|pdf2.dat")
    fd = wx.FileDialog(None, message=_("Open main database file"),
                       defaultFile=INTERNAL["main_file"],
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                       wildcard=wild)
    if fd.ShowModal() == wx.ID_OK:
        fnam = fd.GetPath()
        try:
            indexate_with_progress(fnam, indnam, indnam_d)
        except (ValueError, IndexError):
            wx.MessageBox(_("Wrong database file"), _("Error!"),
                          wx.OK | wx.ICON_ERROR | wx.CENTER)
            return False
        INTERNAL["main_file"] = fnam
        return True
    return False


def indexate_with_progress(in_name, out_name, out_name_d):
    fobj = open(in_name)
    fobj.seek(0, 2)
    epo = fobj.tell()
    lines = float(epo / 80)
    pos = 0
    index = []
    index_d = []
    dialog = wx.ProgressDialog(
        _("Indexator"), _("Indexing database..."), 100,
        style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
    nextp = 1
    while pos >= 0:
        card = NIST_Card()
        ppos = pos
        pos = card.set_by_NIST_file(fobj, ppos, False)
        els = card.get_formula_elements()
        if els:
            if card.deleted:
                index_d.append((els, ppos))
            else:
                index.append((els, ppos))
        if pos / lines * 100. >= nextp:
            dialog.Update(nextp)
            nextp += 1
    fobj.close()
    dialog.Destroy()
    with open(out_name, 'wb') as fpt:
        dump(index, fpt)
    with open(out_name_d, 'wb') as fpt:
        dump(index_d, fpt)


class RHListCtrl(wx.ListCtrl, ListRowHighlighter):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ListRowHighlighter.__init__(self)
        self.SetHighlightColor("light gray")


class DBCardsList:
    def __init__(self, internal, index):
        self.internal = internal
        parent = internal['window']
        self.__el_index = index
        if not self.__el_index:
            return
        self.__parent = parent
        self.__plot = internal['plot']
        self.__data = internal['data']
        self.__mname = _("NIST Pattern")
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
        self.card_poss = {}
        self.__alive = True
        self.html_mdi = None

    def __nonzero__(self):
        return self.__alive

    def plot_pattern(self, unum):
        "plot the current pattern"
        print("plot %s" % unum)
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
            if 'wavelength' in cd.tech_info and not chromos:
                chromos = [(cd.tech_info['wavelength'], 1.)]
                wavels = [cd.tech_info['wavelength']]
            if 'wavelength' in cd.tech_info:
                wavel = cd.tech_info['wavelength']
        if pln and pln != mpln and units in (
                'A', 'A^{-1}', 'sin(\\theta)',
                '2\\theta', '\\theta') and not cd.ax2:
            colors = ("red", "orange", "green")
            cd = cd.clone()
            for clr, (wavel, intens) in enumerate(chromos):
                x, y = self.card_poss[unum].get_di(units, wavel)
                y *= intens
                cd.append((x, y, 2, colors[clr], 'pulse'))
            cd.set_info(self.card_poss[unum].wiki_di(units, wavels, cd))
            plt.set_data(mpln, cd)
            plt.plot_dataset(mpln)
            return
        if mpln in plt:
            cd = plt.get_data(mpln)
            if 'wavelength' in cd.tech_info:
                wavel = cd.tech_info['wavelength']
            units = cd.get_units()
            last = []
            if not chromos:
                chromos = [(0., 1.)]
                wavels = [0]
            for wavel, intens in chromos:
                x, y = self.card_poss[unum].get_di(units, wavel)
                y *= intens
                last.append((x, y))
            cd.replace_last(last)
            cd.set_info(self.card_poss[unum].wiki_di(units, wavels, cd))
            plt.plot_dataset(mpln)
            return
        x, y = self.card_poss[unum].get_di('A^{-1}', 0.)
        plt.set_data(mpln, [(x, y, 1, None, 'pulse')], r'$\AA^{-1}$',
                     'I, %', 'A^{-1}')
        plt.get_data(mpln).set_info(
            self.card_poss[unum].wiki_di('A^{-1}', [0]))
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
        del self.card_poss

    def Raise(self):
        self.__frame.Raise()

    def filter_elments(self, evt=None):
        if 'GetKeyCode' in dir(evt) and \
                evt.GetKeyCode() not in [0, wx.WXK_RETURN]:
            evt.Skip()
            return
        text = self.filter.GetValue()
        incl_del = self.incl_del.IsChecked()
        self.filter.SetValue("")
        elfilter = ElFilter(text)
        if incl_del:
            el_ind = self.__el_index[0] + self.__el_index[1]
        else:
            el_ind = self.__el_index[0]
        if elfilter:
            positions = [pos for els, pos in el_ind if elfilter(els)]
        else:
            return
        fobj = open(self.internal["main_file"])
        for pos in positions:
            card = NIST_Card()
            card.set_by_NIST_file(fobj, pos, num_only=True)
            unum = card.get_unumber()
            # maybe it should be virtual list
            # but now max number of items will be limited
            max_items = 300
            prev_poss = self.card_poss.keys()
            if unum not in prev_poss:
                card.set_by_NIST_file(fobj, pos)
                card.cl_pos = pos
                self.card_poss[unum] = card
                index = self.__list.InsertStringItem(sys.maxint, unum)
                self.__list.SetStringItem(index, 1, card.get_uname())
                self.__list.SetStringItem(index, 2, card.get_uformula())
                qual = card.quality + (card.deleted and u"\u22a0" or u"\u22a1")
                self.__list.SetStringItem(index, 3, qual)
                if index > max_items:
                    break
        self.__list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.__list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.__list.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        fobj.close()
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
                unum = self.__list.GetItemText(p)
                self.__list.DeleteItem(p)
                del self.card_poss[unum]
            self.__list.RefreshRows()
        if action is "Info":
            self.info_window(unum)
        if action is "Clear":
            self.__list.DeleteAllItems()
            self.card_poss.clear()
        if action is "prepos":
            self.predefine_reflexes(unum)

    def list_event(self, event):
        k_code = event.GetKeyCode()
        index = event.GetIndex()
        unum = event.GetText()
        if k_code == wx.WXK_DELETE:
            self.__list.DeleteItem(index)
            del self.card_poss[unum]
            self.__list.RefreshRows()
        elif k_code == ord('i') or k_code == ord('I'):
            self.info_window(unum)
        elif k_code == ord('X'):
            self.__list.DeleteAllItems()
            self.card_poss.clear()
        elif k_code == ord('D'):
            with open(self.internal["main_file"]) as fobj:
                print(string_card(fobj, self.card_poss[unum].cl_pos))
        elif k_code == wx.WXK_RETURN or k_code == 0:
            self.plot_pattern(unum)

    def info_window(self, unum):
        if not unum:
            return
        card = self.card_poss[unum]
        popnew = True
        for htmw in self.__htmlist:
            if htmw.popup(card):
                popnew = False
                break
        if popnew:
            if not self.html_mdi:
                self.html_mdi = HTML_MDI(self.__frame)
            html = HTML_CardInfo(self.html_mdi, card, self.__htmlist)
            self.__htmlist.append(html)

    def predefine_reflexes(self, unum):
        if not unum:
            return
        card = self.card_poss[unum]
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
        for reflex in card.reflexes:
            p = wavel / reflex[0]
            if p > 1.:
                continue
            i = float(reflex[1])
            if len(reflex) == 2:
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
        self.Show()

    def __nonzero__(self):
        return self.alive

    def on_window_close(self, evt):
        "closing and making self False"
        self.Destroy()
        self.alive = False


class HTML_CardInfo(wx.MDIChildFrame):
    def __init__(self, parent, card, htmlist):
        self.htmlist = htmlist
        self.card = card
        self.parent = parent
        wx.MDIChildFrame.__init__(self, parent, -1, card.get_unumber())
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        html.SetPage(self.mkhtext())
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_window_destroy)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.parent.Raise()
        self.Show()

    def on_char(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.Destroy()
        evt.Skip()

    def on_window_destroy(self, evt=None):
        self.htmlist.remove(self)

    def popup(self, card):
        if self.card is card:
            self.parent.Raise()
            self.Activate()
            return True
        return False

    def mkhtext(self):
        qual = self.card.quality
        if self.card.deleted:
            qual += _(" (Deleted)")
        res = _("""
<table>
<tr><td>Number:</td><td>%(num)s</td></tr>
<tr><td>Name:</td><td>%(nam)s</td></tr>
<tr><td>Formula:</td><td>%(fml)s</td></tr>
<tr><td>Quality:</td><td>%(qlt)s</td></tr>
""") %\
            {'num': self.card.get_unumber(), 'nam': self.card.get_uname(),
             'fml': self.card.get_uformula_markup(), 'qlt': qual}
        if self.card.cellparams:
            pnr = ['a', 'b', 'c', u'\u03b1', u'\u03b2', u'\u03b3']
            res += "<tr><td>%s</td><td>" % _("Cell parameters:")
            ppr = []
            for i in xrange(6):
                if self.card.cellparams[i]:
                    ppr.append("%s=%s" % (
                        pnr[i], locale.format("%g", self.card.cellparams[i])))
            res += "; ".join(ppr) + "</td></tr>\n"
        if self.card.spc_grp:
            res += "<tr><td>%s</td><td>%s</td></tr>\n" % \
                (_("Space group:"), self.card.spc_grp)
        res += "</table>\n"
        if self.card.reflexes:
            rtbl = "<br>\n<br>\n<table border=1>\n"
            rtblr = "<tr>"
            rcels = 0
            for reflex in self.card.reflexes:
                if len(reflex) == 2:
                    rtblr += "<td><pre> %s %3d </pre></td>" % \
                        ((locale.format("%.5f", reflex[0]),) + reflex[1:])
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
        if self.card.comment:
            res += _("<h5>Comment</h5>")
            for cod, val in self.card.get_umcomment():
                if cod == 'CL':
                    res += _("Color: ")
                res += val + "<br>\n"
        if self.card.ref:
            res += _("<h5>References</h5>\n")
            codens = get_codens_dict()
            res += "<ul>\n"
            for ref in self.card.ref:
                lit = "<li>"
                if ref["names"]:
                    lit += "%s // " % ref["names"]
                if ref["code"] in codens:
                    lit += codens[ref["code"]]
                else:
                    lit += ref["code"]
                if ref["V"]:
                    lit += ", <b>%s</b>" % ref["V"]
                if ref["P"]:
                    lit += ", P. %s" % ref["P"]
                if ref["Y"]:
                    lit += " (%s)" % ref["Y"]
                res += lit + "</li>\n"
            res += "</ul>\n"
        return ''.join(['<html><body>', res, "</body></html>"])
