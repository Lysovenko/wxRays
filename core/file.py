#!/usr/bin/env python
"""Read data files"""
# wxRays (C) 2013-2015 Serhii Lysovenko
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

import numpy as np


def ascii_file_load(fname):
    arr = []
    odict = {}
    try:
        fobj = open(fname)
    except IOError:
        return None, None, odict
    with fobj:
        for l in fobj:
            if l.startswith('#'):
                spl = l[1:].split(':', 1)
                if len(spl) == 2:
                    odict[spl[0].strip()] = spl[1].strip()
                continue
            try:
                spl = l.split()
                x, y = map(float, spl)[:2]
                arr.append((x, y))
            except ValueError:
                pass
    if arr:
        arr.sort()
        arr = np.array(arr)
        x = arr.transpose()[0]
        y = arr.transpose()[1]
    else:
        x, y = None, None
    return x, y, odict


def save_dat(name, tpl, comment=None):
    with open(name, "w") as fpt:
        if comment is not None:
            scm = comment.encode("utf8")
            for itm in scm.split('\n'):
                if itm:
                    fpt.write('# %s\n' % itm)
        if type(tpl[-1]) == dict:
            for i, v in tpl[-1].items():
                if type(v) in (int, float, tuple):
                    fpt.write('#%s: %s\n' % (str(i), repr(v)))
                elif type(v) in (str, unicode):
                    fpt.write('#%s: %s\n' % (str(i), v.encode("utf8")))
            tpl = tpl[:-1]
        if type(tpl[0]) == tuple:
            for tup in tpl:
                if len(tup) > 2:
                    fpt.write("# %s\n" % tup[2])
                for i in zip(*tup[:2]):
                    fpt.write("%g\t%g\n" % i)
                fpt.write("\n\n")
        else:
            fstr = "%g" + "\t%g" * (len(tpl) - 1) + "\n"
            for itm in zip(*tpl):
                fpt.write(fstr % itm)


class Exp_Data:
    def __init__(self, fname, loaders):
        x = None
        y = None
        dct = {}
        for loader in loaders:
            x, y, dct = loader(fname)
            if x is not None and y is not None:
                break
        self.name = unicode(fname)
        self.elements = None
        self.rho0 = None
        self.__sample = None
        self.__dict = {}
        self.x_data = x
        self.y_data = y
        self.wavel = None
        # diffraction angle of monochromer
        self.alpha = None
        self.x_axis = None
        self.lambda1 = None
        self.lambda2 = None
        self.lambda3 = None
        self.sm_pars = None
        self.I2 = .5
        self.I3 = .2
        self.set_dict(dct)

    def __nonzero__(self):
        if self.y_data is None:
            return False
        if self.x_axis == "q":
            return True
        return bool(self.wavel and self.x_axis)

    def __len__(self):
        return len(self.x_data)

    def get_qrange(self):
        if not self:
            return None
        if self.x_axis == "q":
            return self.x_data
        if self.x_axis == "2\\theta":
            acoef = np.pi / 360.
        if self.x_axis == "\\theta":
            acoef = np.pi / 180.
        K = 4. * np.pi / self.wavel
        return K * np.sin(self.x_data * acoef)

    def get_theta(self):
        if self.x_axis == "q":
            return None
        if self.x_axis == "2\\theta":
            acoef = np.pi / 360.
        elif self.x_axis == "\\theta":
            acoef = np.pi / 180.
        return np.array(self.x_data) * acoef

    def get_2theta(self):
        if self.x_axis == "q":
            return None
        if self.x_axis == "2\\theta":
            acoef = np.pi / 180.
        elif self.x_axis == "\\theta":
            acoef = np.pi / 90.
        return np.array(self.x_data) * acoef

    def get_y(self):
        return self.y_data

    def corr_intens(self):
        """correct intensity"""
        Iex = self.y_data
        ang = self.get_2theta()
        if self.alpha is None:
            return Iex / (np.cos(ang) ** 2 + 1.) * 2.
        c2a = np.cos(2. * self.alpha) ** 2
        return Iex / (c2a * np.cos(ang) ** 2 + 1.) * (1. + c2a)

    def rev_intens(self, Icor):
        """reverse correct intensity"""
        ang = self.get_2theta()
        if self.alpha is None:
            return Icor / 2. * (np.cos(ang) ** 2 + 1.)
        c2a = np.cos(2. * self.alpha) ** 2
        return Icor * (c2a * np.cos(ang) ** 2 + 1.) / (1. + c2a)

    def get_dict(self):
        return self.__dict

    def set_dict(self, dct):
        self.__dict.update(dct)
        if 'lambda1' in dct:
            try:
                self.lambda1 = float(dct['lambda1'])
            except ValueError:
                pass
        if 'lambda2' in dct:
            try:
                self.lambda2 = float(dct['lambda2'])
            except ValueError:
                pass
        if 'lambda3' in dct:
            try:
                self.lambda3 = float(dct['lambda3'])
            except ValueError:
                pass
        if 'lambda' in dct:
            try:
                self.wavel = float(dct['lambda'])
            except ValueError:
                pass
        if 'alpha' in dct:
            try:
                self.alpha = float(dct['alpha']) * np.pi / 180.
            except ValueError:
                pass
        if 'I2' in dct:
            try:
                self.I2 = float(dct['I2'])
            except ValueError:
                pass
        if 'I3' in dct:
            try:
                self.I3 = float(dct['I3'])
            except ValueError:
                pass
        if 'x_axis' in dct:
            if dct['x_axis'] in ['2\\theta', "\\theta", "q"]:
                self.x_axis = dct['x_axis']
            else:
                self.x_axis = None
        if 'elements' in dct:
            try:
                self.elements = eval(dct['elements'])
            except SyntaxError:
                self.elements = None
        if 'rho0' in dct:
            self.rho0 = float(dct['rho0'])
        if 'sample' in dct:
            self.__sample = dct['sample'].lower()
        if 'name' in dct:
            self.name = dct['name'].decode('utf8')
        if not self.wavel:
            self.wavel = self.lambda1
        if not self.lambda1:
            self.lambda1 = self.wavel

    def is_sample(self, sample, default=True):
        if self.__sample is None:
            return default
        return self.__sample == sample.lower()

    def add_multiple_data(self, data):
        allow = [i for i in data if i.x_axis == self.x_axis]
        if len(allow) == 0:
            return False
        sumlist = list(zip(self.x_data, self.y_data))
        for i in allow:
            sumlist += list(zip(i.x_data, i.y_data))
        sumlist.sort()
        xo, yo = sumlist[0]
        rlist = []
        sames = 1.
        for xl, yl in sumlist[1:]:
            if xo != xl:
                rlist.append((xo, yo))
                xo = xl
                yo = yl
                sames = 1.
            else:
                sames += 1.
                yo += (yl - yo) / sames
        if sames > 1:
            rlist.append((xo, yo))
        self.x_data, self.y_data = np.array(rlist).transpose()
        return True
