#!/usr/bin/env python
# -*- coding: utf-8 -*-
" Some predefined dialogs "
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
import wx.lib.rcsizer as rcs
import locale as loc
import os.path as osp
try:
    str = unicode
except NameError:
    pass


class ValidFloat(wx.PyValidator):
    "validator for floating point fields"
    def __init__(self, is_ipos=lambda x: x <= 0., can_empty=False):
        wx.PyValidator.__init__(self)
        self.err_msg = ""
        self.is_impossible = is_ipos
        self.can_empty = can_empty

    def Clone(self):
        return ValidFloat(self.is_impossible, self.can_empty)

    def Validate(self, win):
        text_ctrl = self.GetWindow()
        if not text_ctrl.IsEnabled():
            return True
        text = text_ctrl.GetValue()
        if self.test_text(text):
            text_ctrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.Refresh()
            return True
        wx.MessageBox(self.err_msg, _("Error"))
        text_ctrl.SetBackgroundColour("pink")
        text_ctrl.SetFocus()
        text_ctrl.Refresh()
        return False

    def test_text(self, text):
        if len(text) == 0:
            self.err_msg = _("Field is empty.")
            return False
        try:
            flt = atof(text)
        except ValueError:
            self.err_msg = _("Wrong type of float.")
            return False
        if self.is_impossible(flt):
            self.err_msg = _("Unreal value.")
            return False
        return True

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True


def atof(string):
    "stuppid locale's work with unicode is wrong"
    if type(string) == unicode:
        string = string.encode(loc.getlocale(loc.LC_NUMERIC)[1])
    return loc.atof(string)


class DlgDdataFile(wx.Dialog):
    "Missing docstring"
    # Lambda in Angstroms:
    # Cr, Co, Cu, Mo
    # According to the last re-examination of Holzer et al. (1997)
    #    Ka1      Ka2      Kb1
    ANODES = {"Cr": (2.289760, 2.293663, 2.084920, .506, .21),
              "Fe": (1.93604, 1.93998, 1.75661, .491, .182),
              "Co": (1.789010, 1.792900, 1.620830, .532, .191),
              "Cu": (1.540598, 1.544426, 1.392250, .46, .158),
              "Mo": (0.709319, 0.713609, 0.632305, .506, .233),
              "Ni": (1.65784, 1.66169, 1.50010, .476, .171),
              "Ag": (0.55936, 0.56378, 0.49701, .5, .2),
              "W": (0.208992, 0.213813, 0.18439, .5, .2)}
    axes = ["\\theta", "2\\theta", "q"]
    laxes = [u'\u03b8', u'2\u03b8', u'q: 4\u03c0 sin(\u03b8)/\u03bb']

    def __init__(self, parent):
        title = _("Experimental features")
        wx.Dialog.__init__(self, parent, -1, title)
        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, _("Radiation"))
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Anticatode:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sample_list = self.ANODES.keys()
        sample_list.sort()
        self.anode = wx.Choice(self, -1, choices=sample_list)
        item = APP_SETT.get("dlg_data_file_anode", 0)
        if 0 > item >= len(sample_list):
            item = 0
        self.anode.SetSelection(item)
        box.Add(self.anode, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("Filtering:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        filterings = [_("Monochromator"), _("Alpha mix"), _("No beta-filter")]
        self.filtering = wx.Choice(self, -1, choices=filterings)
        item = APP_SETT.get("dlg_data_file_filtering", 0)
        if 0 > item or item >= len(filterings):
            item = 0
        self.filtering.SetSelection(item)
        box.Add(self.filtering, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT |
                  wx.TOP, 5)
        # Axis units selection
        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, _("File X:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.abscissa = wx.Choice(self, -1, choices=self.laxes)
        item = APP_SETT.get("dlg_data_file_abscissa", 0)
        if 0 > item >= len(self.laxes):
            item = 0
        self.abscissa.SetSelection(item)
        box.Add(self.abscissa, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(self, -1, _("Sample:")),
                0, wx.ALIGN_CENTRE | wx.ALL, 5)
        samples = [_("Powder"), _("Liquid")]
        self.sample = wx.Choice(self, -1, choices=samples)
        item = APP_SETT.get("dlg_data_file_sample", 0)
        if 0 > item or item >= len(samples):
            item = 0
        self.sample.SetSelection(item)
        box.Add(self.sample, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT |
                  wx.TOP, 5)
        # Buttons...
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_wavelength(self, dct={}):
        "Missing docstring"
        anode = self.anode.GetSelection()
        arays = self.ANODES[self.anode.GetString(anode)]
        rays = self.filtering.GetSelection()
        if rays == 0:
            return arays[0]
        if rays == 1:
            dct["lambda1"], dct["lambda2"] = arays[:2]
            dct["I2"] = arays[3]
        if rays == 2:
            dct["lambda1"], dct["lambda2"], dct["lambda3"] = arays[:3]
            dct["I2"], dct["I3"] = arays[3:5]
        return (arays[0] + arays[1] * dct["I2"]) / (1. + dct["I2"])

    def get_dict(self):
        "Missing docstring"
        samples = ["powder", "liquid"]
        dct = {}
        dct["lambda"] = self.get_wavelength(dct)
        dct["x_axis"] = self.axes[self.abscissa.GetSelection()]
        dct["sample"] = samples[self.sample.GetSelection()]
        return dct

    def save_choice(self):
        "Missing docstring"
        item = self.anode.GetSelection()
        APP_SETT.set("dlg_data_file_anode", item)
        item = self.filtering.GetSelection()
        APP_SETT.set("dlg_data_file_filtering", item)
        item = self.abscissa.GetSelection()
        APP_SETT.set("dlg_data_file_abscissa", item)
        APP_SETT.set("dlg_data_file_sample", self.sample.GetSelection())


class DlgProgressCallb:
    def __init__(self, parent, title, message, maximum, can_abort=False,
                 cumulative=False):
        style = wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        if can_abort:
            style |= wx.PD_CAN_ABORT
        self.dialog = wx.ProgressDialog(title, message, maximum, parent,
                                        style=style)
        self.maximum = maximum
        if cumulative:
            self.cur_pos = 0
        else:
            self.cur_pos = None
        self.state = True

    def __call__(self, nextp):
        if self.cur_pos is None:
            res = self.dialog.Update(nextp)[0]
        else:
            self.cur_pos += 1
            res = self.dialog.Update(self.cur_pos)[0]
        self.state = res
        if self.maximum == nextp or not res:
            self.dialog.Destroy()
        return res

    def __nonzero__(self):
        return self.state


def make_mask(loads):
    ake = set()
    for l in loads:
        for i in l[1]:
            ake.add(i)
    oarr = [_('All known filetypes')]
    elst = []
    for i in ake:
        elst.append('*%s' % i)
    oarr.append(';'.join(elst))
    for l in loads:
        oarr.append(l[0])
        elst = []
        for i in l[1]:
            elst.append('*%s' % i)
        oarr.append(';'.join(elst))
    return '|'.join(oarr)


def load_data_file(mobj, fnames, loads):
    if fnames is None:
        prev_dir = eval(APP_SETT.get("df_prev_dir", "''"))
        wild = make_mask(loads)
        fd = wx.FileDialog(mobj, message=_("Open data file(s)"),
                           style=wx.FD_OPEN | wx.MULTIPLE,
                           wildcard=wild, defaultDir=prev_dir)
        index = fd.GetFilterIndex()
    else:
        index = 0
    if fnames is not None or fd.ShowModal() == wx.ID_OK:
        from ..file import Exp_Data
        from .plot import plot_exp_data
        if fnames is None:
            fnams = fd.GetPaths()
            APP_SETT.set("df_prev_dir", repr(fd.GetDirectory()))
        else:
            fnams = fnames
        ldrs = [i[2] for i in loads]
        if index > 0:
            ldr = loads[index - 1][2]
            if ldr in ldrs:
                ldrs.insert(0, ldrs.pop(ldrs.index(ldr)))
            else:
                ldrs.insert(0, ldr)
        datas = []
        err_fnams = []
        for i in fnams:
            data = Exp_Data(i, ldrs)
            if data.y_data is not None:
                datas.append(data)
            else:
                err_fnams.append(i)
        if len(err_fnams) > 0:
            wx.MessageBox(_("Wrong data file(s):\n%s") %
                          u"\n".join(err_fnams), _("Error!"),
                          wx.OK | wx.ICON_ERROR | wx.CENTER)
        if len(datas) > 0:
            data = datas[0]
        else:
            data = None
        if len(datas) > 1:
            if not data.add_multiple_data(datas[1:]):
                wx.MessageBox(
                    _("Other data are incompatible to the\n%s") %
                    fnams[0], _("Error!"), wx.OK | wx.ICON_ERROR | wx.CENTER)
        if data is None:
            return
        if not data:
            from .dialogs import DlgDdataFile
            dlg = DlgDdataFile(mobj)
            if dlg.ShowModal() == wx.ID_OK:
                dct = dlg.get_dict()
                dlg.save_choice()
                data.set_dict(dct)
            else:
                return
        plot_exp_data(mobj.plot, data, mobj.a_menu)
        mobj.data["Exp. data"] = data
        mobj.SetTitle(u"%s: %s" % (PROG_NAME, data.name))


def about_box():
    # First we create and fill the info object
    from settings import VERSION
    info = wx.AboutDialogInfo()
    info.Name = PROG_NAME
    info.Version = VERSION
    info.Copyright = _("(C) 2013-2014 Serhii Lysovenko")
    info.Description = _("Treater of the x-ray diffraction data")
    info.WebSite = ("http://sourceforge.net/p/wxrays", _("Home page"))
    lfp = open(osp.join(osp.dirname(__file__), "__main__.py"))
    tfl = ''
    while "wxRays" not in tfl:
        tfl = lfp.readline()
    licenseText = []
    while tfl[0] == '#':
        licenseText.append(tfl[1:].strip())
        tfl = lfp.readline()
    lfp.close()
    info.License = '\n'.join(licenseText)
    wx.AboutBox(info)


class InputElement:
    "element of \"Input\" dialog"
    def __init__(self, parent, args):
        data = args[1]
        typed = type(data)
        if typed == list:
            if len(args) > 2:
                defitem = args[2]
            else:
                defitem = 0
            self.input = wx.Choice(parent, -1, choices=data)
            self.input.SetSelection(defitem)
            self.this_is = "list"
        elif typed == int:
            vmin, vmax = (args[2:] + (0, 100)[len(args) - 2:])[:2]
            self.input = wx.SpinCtrl(parent)
            self.input.SetRange(vmin, vmax)
            self.input.SetValue(data)
            self.this_is = "int"
        elif typed == float:
            if type(args[-1]) != float:
                badv = args[-1]
                args = args[:-1]
            else:
                def badv(x): return False
            if len(args) == 2:
                tdata = loc.format(u"%g", data)
                self.input = wx.TextCtrl(parent, value=tdata,
                                         validator=ValidFloat(is_ipos=badv))
            else:
                tdata = [loc.format(u"%g", i) for i in args[1:]]
                self.input = wx.ComboBox(
                    parent, value=tdata[0], choices=tdata,
                    style=wx.CB_DROPDOWN, validator=ValidFloat(is_ipos=badv))
            self.this_is = "float"
        elif typed == bool:
            self.input = wx.CheckBox(parent, -1, args[0])
            self.input.SetValue(data)
            self.this_is = "boolean"
        else:
            raise TypeError("Type is %s, only list, int or float expected"
                            % str(typed))
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        if typed != bool:
            label = wx.StaticText(parent, -1, args[0])
            self.box.Add(label, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        self.box.Add(self.input, 1, wx.ALIGN_RIGHT | wx.ALL, 5)

    def get_value(self):
        if self.this_is == "list":
            return self.input.GetCurrentSelection()
        if self.this_is == "float":
            return atof(self.input.GetValue())
        return self.input.GetValue()


class DlgInput(wx.Dialog):
    "Input dialog box"
    def __init__(self, parent, title, args):
        wx.Dialog.__init__(self, parent, -1, title)
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.inputs = []
        for i in args:
            itm = InputElement(self, i)
            self.inputs.append(itm)
            sizer.Add(itm.box, 0,
                      wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        # Buttons...
        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_CANCEL)
        box.Add(btn, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        box.Add(btn, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(box, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)


def v_input(parent, title, *args):
    dlg = DlgInput(parent, title, args)
    if dlg.ShowModal() == wx.ID_OK:
        return tuple([i.get_value() for i in dlg.inputs])


class DlgPuzzle(wx.Dialog):
    "Input dialog box"
    def __init__(self, parent, puzzle):
        wx.Dialog.__init__(self, parent, -1, "")
        if parent is not None:
            self.SetIcon(parent.GetIcon())
        self.current_table = None
        self.current_raw = -1
        self.row_spans = {}
        puzzle.set_actors({
            'set_title': self.SetTitle,
            'table_new': self.new_table,
            'table_end': self.end_table,
            'table_next_raw': self.table_next_raw,
            'table_put_cell': self.table_put_cell,
            'get_label': self.get_label,
            'get_text': self.get_text,
            'get_spin': self.get_spin,
            'get_button': self.get_button,
            'get_radio': self.get_radio,
            'get_line': self.get_line})
        puzzle.play()

    def new_table(self):
        self.current_table = rcs.RowColSizer()

    def end_table(self):
        self.current_table.RecalcSizes()
        self.SetSizer(self.current_table)
        self.current_table.Fit(self)

    def table_next_raw(self):
        self.current_raw += 1
        self.current_col = 0
        for i in list(self.row_spans.keys()):
            self.row_spans[i][1] -= 1
            if self.row_spans[i][1] == 0:
                self.row_spans.pop(i)
        while self.current_col in self.row_spans:
            self.current_col += self.row_spans[self.current_col][0]

    def table_put_cell(self, cont, align, colspan,
                       rowspan, expand, border):
        flag = wx.ALL
        if expand:
            flag = wx.EXPAND
        if align == "right":
            flag |= wx.ALIGN_RIGHT
        if align == "center":
            flag |= wx.ALIGN_CENTER
        if colspan is None:
            colspan = 1
        if rowspan is None:
            rowspan = 1
        if not border:
            border = 0
        self.current_table.Add(
            cont, row=self.current_raw, col=self.current_col,
            flag=flag, colspan=colspan, rowspan=rowspan, border=border)
        self.row_spans[self.current_col] = [colspan, rowspan]
        while self.current_col in self.row_spans:
            self.current_col += self.row_spans[self.current_col][0]

    def get_label(self, label):
        return wx.StaticText(self, -1, label)

    def get_text(self, value):
        txt = wx.TextCtrl(self, value=str(value))
        txt.wxrd_value = value
        txt.Bind(wx.EVT_TEXT, self.text_changed)
        return txt

    def get_spin(self, begin=0, end=0, value=0):
        spin = wx.SpinCtrl(self, -1)
        spin.SetRange(begin, end)
        spin.SetValue(value)
        return spin

    def get_button(self, b_type, default=False):
        types = {"OK": wx.ID_OK, "Cancel": wx.ID_CANCEL}
        btn = wx.Button(self, types[b_type])
        if default:
            btn.SetDefault()
        return btn

    def get_radio(self, title, options, default, vertical, onchange):
        radio = wx.RadioBox(self, -1, title, choices=options, majorDimension=2,
                            style=wx.RA_SPECIFY_COLS)
        return radio

    def get_line(self):
        return wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)

    def text_changed(self, evt):
        text_ctrl = evt.EventObject
        val = text_ctrl.wxrd_value
        try:
            val.update(text_ctrl.GetValue())
        except ValueError as err:
            text_ctrl.SetBackgroundColour("pink")
            text_ctrl.Refresh()
        else:
            text_ctrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            text_ctrl.Refresh()
        print(val)
