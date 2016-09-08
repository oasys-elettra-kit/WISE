#! /usr/bin/env python3

import os

from setuptools import find_packages, setup

NAME = 'OASYS-WISE'
VERSION = '1.0.6'
ISRELEASED = True

DESCRIPTION = 'WISE in Python'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Michele Manfredda, Lorenzo Raimondi, Luca Rebuffi'
AUTHOR_EMAIL = 'luca.rebuffi@elettra.eu'
URL = 'https://github.com/lucarebuffi/WISE'
DOWNLOAD_URL = 'https://github.com/lucarebuffi/WISE'
LICENSE = 'GPLv3'

KEYWORDS = (
    'waveoptics',
    'simulator',
    'oasys',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'setuptools',
    'numpy',
    'scipy',
    'matplotlib==1.4.3',
    'srxraylib>=0.0.9',
    'orange-widget-core>=0.0.2',
    'oasys>=0.1.18',
    'wiselib',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.wise.widgets.wise":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.wise.widgets.tools":["icons/*.png", "icons/*.jpg"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.wise", "orangecontrib.wise.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("wise = orangecontrib.wise", ),
    'oasys.widgets' : (
        "WISE = orangecontrib.wise.widgets.wise",
        "WISE Tools = orangecontrib.wise.widgets.tools",
    ),
}

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          #          py_modules = PY_MODULES,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          #extras_require = EXTRAS_REQUIRE,
          #dependency_links = DEPENDENCY_LINKS,
          entry_points = ENTRY_POINTS,
          namespace_packages=NAMESPACE_PACAKGES,
          include_package_data = True,
          zip_safe = False,
          )