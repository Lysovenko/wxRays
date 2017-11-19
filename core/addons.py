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

from __future__ import print_function, absolute_import
from sys import modules, path
from imp import find_module, load_module
from os import listdir
from os.path import (dirname, realpath, split, splitext, join, isfile,
                     isabs, normpath)


class Addons:
    def __init__(self):
        "searches and reads addons descriptions files"
        pth1 = join(dirname(dirname(realpath(__file__))), 'addons')
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
                    try:
                        add_descr[ls[0]] = unicode(ls[1].strip(), 'utf-8')
                    except NameError:
                        add_descr[ls[0]] = ls[1].strip()
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
                except ImportError as err:
                    desc['isactive'] = False
                    any_error = True
                    print('ImportError: %s, %s' % (nam, err))
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
