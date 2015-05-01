wxRays
======

* Homepage: https://sourceforge.net/p/wxrays/wiki/Home/
* https://sourceforge.net/p/wxrays/code/ (primary)
* https://github.com/Lysovenko/wxRays (mirror)

X-rays Python educational project.

Dependencies
============

* [Python](http://python.org)
* [wxPython](http://www.wxpython.org/)
* [NumPy](http://www.numpy.org/)
* [SciPy](http://www.scipy.org/)
* [Mathplotlib](http://matplotlib.org/)

Usage
=====

This is a GUI based program - nothing to explain ;-)

Installing
==========

Get the Snapshot or clone the repository in your option.
To install the package for whole system just make appropriate binary package:
<code>
    ~$ python setup.py bdist_rpm    
</code>
and install it.

Addons
------

An addon consists of the <code>&lt;addon_name&gt;.addon</code> file which
contains the description of the addon and one or few <code>*.py</code> files.
Place the addons files to the directory where the program files are placed and
activate in the appropriate dialog window. Addon's files also can be placed to
the folder where the program saves its settings. In POSIX systems setting files
placed in <code>~/.wxRays</code> or <code>~/.config/wxRays</code> directory, in
other systems they placed in the <code>wxRays</code> folder, which is placed in
the user's home directory.

Configuration
=============

Tools-&gt;Addons

Check required. Also wxRays remembers your options.
