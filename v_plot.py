# wxRays (C) 2013 Serhii Lysovenko
#
"operating with plot on main frame"
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
#
# If matplotlib contributes to a project that leads to a scientific
# publication, please acknowledge this fact by citing the project.
# You can use this BibTeX entry:
# @Article{Hunter:2007,
#   Author    = {Hunter, J. D.},
#   Title     = {Matplotlib: A 2D graphics environment},
#   Journal   = {Computing In Science \& Engineering},
#   Volume    = {9},
#   Number    = {3},
#   Pages     = {90--95},
#   abstract  = {Matplotlib is a 2D graphics package used for Python
#   for application development, interactive scripting, and
#   publication-quality image generation across user
#   interfaces and operating systems.},
#   publisher = {IEEE COMPUTER SOC},
#   year      = 2007
# }

import wx
from formtext import wiki2html
from wx.html import HtmlWindow
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, \
    NavigationToolbar2WxAgg


class Plot:
    'Plot and toolbar'
    def __init__(self, menu=None):
        self.figure = Figure()
        self.toolbar = None
        self.mk_axes()
        self.canvas = None
        self.cur_xunits = 'A^{-1}'
        self.cur_dset = None
        self.__datasets = {}
        self.__colorcircle = 'b g r c m k'.split()
        self.__menu = menu
        self.__menu_ids = {}
        self.__info_frame = None
        self.__statusbar = None
        menu.add_catcher(self.discard)

    def mk_axes(self):
        self.axes1 = self.figure.add_subplot(111)
        self.axes1.grid(True)
        self.axes2 = None
        self.axes1.set_xlabel(r'$s,\, \AA^{-1}$')
        self.axes1.set_ylabel('Intensity')
        self.I_plot = None
        self.p_plot = None
        self.p_plots = []

    def get_canvas(self, parent, **args):
        if not self.canvas:
            self.canvas = FigureCanvasWxAgg(parent, -1, self.figure, **args)
            self.canvas.mpl_connect('pick_event', self.onpick)
            self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        return self.canvas

    def get_toolbar(self):
        if not self.toolbar:
            self.toolbar = NavigationToolbar2WxAgg(self.figure.canvas)
            self.toolbar.Realize()
            self.id_save = wx.NewId()
            self.id_info = wx.NewId()
            self.toolbar.AddSimpleTool(
                self.id_save, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE),
                _("Save plot as ASCII file"), 'Activate custom contol')
            wx.EVT_TOOL(self.toolbar, self.id_save, self.on_save_dat)
            self.toolbar.AddSimpleTool(
                self.id_info, wx.ArtProvider.GetBitmap(wx.ART_INFORMATION),
                _("Details"), 'Activate custom contol')
            wx.EVT_TOOL(self.toolbar, self.id_info, self.on_plot_info)
            self.toolbar.EnableTool(self.id_save, False)
            self.toolbar.EnableTool(self.id_info, False)
        return self.toolbar

    def mk_menuitems(self):
        menu = self.__menu
        menu.add_item(
            "plot", {"!pl info off": False, "!pl info on": True},
            _("Details\tCtrl+D"), self.on_plot_info, wx.ART_INFORMATION)
        menu.add_item(
            "plot", {"!pl sav d off": False, "!pl sav d on": True},
            _("Save plot as ASCII file"), self.on_save_dat, wx.ART_FILE_SAVE)
        menu.action_catch("!pl info off")
        menu.action_catch("!pl sav d off")
        menu.add_item("plot", None, None, None)

    def on_save_dat(self, evt):
        if self.cur_dset is None:
            return
        import os.path as osp
        wild = 'dat|*.dat'
        fd = wx.FileDialog(
            self.canvas,
            message=_(u"Save plot \u201C%s\u201D as ASCII file")
            % self.cur_dset,
            style=wx.FD_SAVE, wildcard=wild, defaultDir='')
        if fd.ShowModal() == wx.ID_OK:
            fnam = fd.GetPath()
            if fnam[-4:] != '.dat':
                fnam += '.dat'
            if osp.isfile(fnam) and  \
                    wx.MessageBox(
                        _(u"""File \u201C%s\u201D already exists.
Rewrite it?""") % osp.basename(fnam), PROG_NAME,
                        wx.YES_NO | wx.ICON_EXCLAMATION) == wx.NO:
                    fd.Destroy()
                    return
            from c_file import save_dat
            data = self.__datasets[self.cur_dset]
            x = data.plots[0][0]
            lx = len(x)
            comment = unicode(data.info)
            dct = data.tech_info
            if all([lx == len(i[0]) and
                    (x == i[0]).all() for i in data.plots]):
                tpl = [x] + [i[1] for i in data.plots]
            else:
                tpl = [i[:2] for i in data.plots]
            save_dat(fnam, tpl + [dct], comment)
        fd.Destroy()

    def on_plot_info(self, evt):
        if self.cur_dset is None:
            return
        info = unicode(self.__datasets.get(self.cur_dset).info)
        if info is None:
            return
        ifr = self.__info_frame
        if ifr:
            ifr.set_infotext(info, self.cur_dset)
        else:
            ifr = Plot_info(self.canvas)
            self.__info_frame = ifr
            ifr.set_infotext(info, self.cur_dset)

    def plot_dataset(self, d_set):
        if d_set not in self.__datasets:
            return
        data = self.__datasets[d_set]
        self.__menu.action_catch("on plot", d_set)
        # enabling on_save_dat, on_plot_info
        self.toolbar.EnableTool(self.id_save, True)
        self.toolbar.EnableTool(self.id_info, data.info is not None)
        self.__menu.action_catch("!pl sav d on")
        self.__menu.action_catch(data.info is not None and "!pl info on"
                                 or "!pl info off")
        plots = data.plots
        last_only = 0
        the_color = None
        if self.cur_dset == d_set and not data.fresh:
            last_only = data.only_last
            if last_only:
                l_plots = len(self.p_plots) - 1
                for pli in xrange(l_plots, l_plots - last_only, -1):
                    el = self.p_plots[pli][0]
                    if hasattr(el, 'get_color'):
                        the_color = el.get_color()
                    elif hasattr(el, 'get_edgecolor'):
                        the_color = el.get_edgecolor()
                    for i in self.p_plots.pop(pli):
                        i.remove()
            else:
                for i in self.p_plots:
                    for j in i:
                        j.remove()
                del self.p_plots[:]
                lax = plots[-1][2]
        else:
            del self.p_plots[:]
            data.fresh = False
            self.cur_dset = d_set
            self.cur_xunits = data.xunits
            self.figure.clear()
            self.figure.suptitle(d_set, fontdict={"family": "Arial"})
            self.p_plot = None
            self.axes1 = self.figure.add_subplot(111)
            self.axes1.grid(True)
            if data.ax2:
                self.axes2 = self.axes1.twinx()
            else:
                self.axes2 = None
            if data.xlabel:
                self.axes1.set_xlabel(
                    data.xlabel, fontdict={"family": "Arial"})
            if data.ylabel:
                self.axes1.set_ylabel(
                    data.ylabel, fontdict={"family": "Arial"})
            if data.picker is not None:
                self.selected, = self.axes1.plot(
                    [plots[0][0][0]], [plots[0][1][0]], 'o', ms=10,
                    alpha=0.5, color='red', visible=False)
        clr = 0
        clrs = self.__colorcircle
        cll = len(clrs)
        if last_only:
            plots = plots[-last_only:]
        for plot in plots:
            # we dont know length of the plot tuple
            x, y, a, cl, tp, pcr = (plot + (None,) * (6 - len(plot)))[:6]
            if tp:
                ltype = tp
            else:
                ltype = '-'
            if cl:
                color = cl
            elif the_color is not None:
                color = the_color
            else:
                clr %= cll
                color = clrs[clr]
                clr += 1
            if a == 1 or a is None:
                a2p = self.axes1
            elif a == 2:
                a2p = self.axes2
            else:
                continue
            if ltype == 'pulse':
                plto = a2p.bar(x, y, width=0.001, edgecolor=color,
                               align="center")
                self.p_plots.append(plto)
            else:
                plto = a2p.plot(x, y, ltype, color=color, picker=pcr)
                self.p_plots.append(plto)
        if self.canvas:
            self.canvas.draw()

    def set_data(self, name, plots, *args, **dargs):
        if type(plots) == list:
            self.__datasets[name] = DataSet(plots, *args, **dargs)
        else:
            self.__datasets[name] = plots
        if name not in self.__menu_ids.values():
            m_id = self.__menu.add_item("plot", {}, name, self.on_menu)
            self.__menu_ids[m_id] = name
        return self.__datasets[name]

    def keys(self):
        "maybe some addon somewheh will geqire it ;-)"
        return self.__datasets.keys()

    def __contains__(self, key):
        return key in self.__datasets

    def get_data(self, item):
        return self.__datasets.get(item)

    def get_cur_data(self):
        "get current data set"
        return self.__datasets.get(self.cur_dset)

    def get_cur_key(self):
        return self.cur_dset

    def on_menu(self, evt):
        if evt.Id in self.__menu_ids:
            self.plot_dataset(self.__menu_ids[evt.Id])
        else:
            evt.Skip()

    def pop(self, item):
        if item in self.__datasets:
            for m_id in self.__menu_ids:
                if self.__menu_ids[m_id] == item:
                    self.__menu_ids.pop(m_id)
                    self.__datasets.pop(item)
                    self.__menu.remove_id(m_id)
                    break

    def discard(self, discn, *garbage):
        "discards plot on menu event"
        dsets = self.__datasets
        for m_id, name in self.__menu_ids.items():
            if discn in dsets[name].discards:
                self.__menu_ids.pop(m_id)
                dsets.pop(name)
                self.__menu.remove_id(m_id)

    def clear(self):
        for m_id in self.__menu_ids:
            self.__menu.remove_id(m_id)
        self.__menu_ids.clear()
        self.__datasets.clear()

    def onpick(self, event):
        cdata = self.__datasets.get(self.cur_dset)
        if cdata is None or cdata.picker is None:
            return True
        if cdata.picker(event, cdata, self.selected):
            self.canvas.draw()

    def set_statusbar(self, sbar):
        self.__statusbar = sbar

    def on_motion(self, event):
        if self.__statusbar is None:
            return
        if event.inaxes:
            self.__statusbar.SetStatusText("x = %g\ty = %g" %
                                           (event.xdata, event.ydata), 0)
        else:
            self.__statusbar.SetStatusText("", 0)


class DataSet:
    'required by Plot class'
    def __init__(self, plots, xlabel=None, ylabel=None, xunits='A^{-1}'):
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xunits = xunits
        self.plots = plots
        self.fresh = True
        self.ax1 = False
        self.ax2 = False
        self.only_last = False
        self.picker = None
        self.info = None
        self.tech_info = {}
        self.discards = set()
        for a in zip(*self.plots)[2]:
            if a == 1:
                self.ax1 = True
            elif a == 2:
                self.ax2 = True

    def get_units(self):
        return self.xunits

    def clone(self):
        cln = DataSet(list(self.plots), self.xlabel, self.ylabel, self.xunits)
        cln.picker = self.picker
        cln.tech_info.update(self.tech_info)
        return cln

    def append(self, plt):
        self.plots.append(plt)
        a = plt[2]
        if a == 1:
            self.ax1 = True
        elif a == 2:
            self.ax2 = True

    def replace_last(self, plt):
        "insecure replace last plot"
        if type(plt) == tuple:
            pplt = self.plots[-1]
            self.plots[-1] = plt + pplt[len(plt):]
            self.only_last = 1
        else:
            for i, pl in enumerate(plt, len(self.plots) - len(plt)):
                pplt = self.plots[i]
                self.plots[i] = pl + pplt[len(pl):]
            self.only_last = len(plt)

    def set_picker(self, picker):
        self.picker = picker

    def set_info(self, info):
        self.info = info


class Plot_info(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent)
        self.SetIcon(parent.GetParent().GetIcon())
        self.html = HtmlWindow(self, style=wx.html.HW_SCROLLBAR_AUTO)
        if "gtk2" in wx.PlatformInfo:
            self.html.SetStandardFonts()
        self.Bind(wx.EVT_CLOSE, self.on_window_close)
        self.__alive = False

    def set_infotext(self, text, title=""):
        self.SetTitle(_("%(a)s: Plot info (%(b)s)") %
                      {'a': PROG_NAME, 'b': title})
        self.html.SetPage(wiki2html(text))
        self.__alive = True
        self.Show(True)
        self.Raise()

    def __nonzero__(self):
        return self.__alive

    def on_window_close(self, evt=None):
        "closing and making self False"
        del self.html
        self.Destroy()
        self.__alive = False


def plot_exp_data(plot, data, menu):
    x = data.x_data
    y = data.y_data
    ddict = data.get_dict()
    plts = [(x, y, 1)]
    plot.clear()
    tfn = _("Intensity curve")
    params = {
        "q": (r'$s,\, \AA^{-1}$', 'I(s)', 'A^{-1}'),
        "2\\theta": (
            r'$2\theta,\,^{\circ}$', r'$I(2\theta)$', '2\\theta'),
        "\\theta": (r'$\theta,\,^{\circ}$', r'$I(\theta)$', '\\theta')
    }[data.x_axis]
    pdat = plot.set_data(tfn, plts, *params)
    eplts = ddict.pop("extra plots", ())
    for plt in eplts:
        plot.set_data(*plt)
    pdat.tech_info.update(ddict)
    if eplts:
        ddict["extra plots"] = eplts
    pdat.tech_info['wavelength'] = data.wavel
    menu.action_catch("on init")
    if data.is_sample("liquid"):
        menu.action_catch('liq samp')
    if data.is_sample("powder"):
        menu.action_catch('pow samp')
    plot.plot_dataset(tfn)
