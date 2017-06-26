from distutils.core import setup
from settings import VERSION
from os import listdir


setup(name="wxRays",
      author="Serhii Lysovenko",
      version=VERSION,
      license="GPLv3",
      packages=["wxRays"],
      package_data={"wxRays":
                    ["splash.png", "locale/uk/LC_MESSAGES/wxRays.mo",
                     "locale/ru/LC_MESSAGES/wxRays.mo",
                     "po/*.po", "doc/*.pdf", "data/*"] +
                    [i for i in listdir('.') if i.endswith('.addon')]},
      package_dir={"wxRays": ""},
      requires=["wxPython (>=2.8)"],
      url="http://sourceforge.net/p/wxrays")
