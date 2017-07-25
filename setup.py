#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup


NAME = 'OASYS1-WISE'
VERSION = '1.1.3'
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
    'oasys1',
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
    'oasys1>=1.0.18',
    'wiselib>=1.0.5',
    #'wofrywise'
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.wise.widgets.wise":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.wise.widgets.tools":["icons/*.png", "icons/*.jpg"],
    #"orangecontrib.wise.widgets.wofry":["icons/*.png", "icons/*.jpg"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.wise", "orangecontrib.wise.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("wise = orangecontrib.wise", ),
    'oasys.widgets' : (
        "WISE = orangecontrib.wise.widgets.wise",
        "WISE Tools = orangecontrib.wise.widgets.tools",
    #    "WISE Wofry = orangecontrib.wise.widgets.wofry",
    ),
}

if __name__ == '__main__':
    is_beta = False

    try:
        import PyMca5, PyQt4

        is_beta = True
    except:
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

    if is_beta: raise NotImplementedError("This version of WISE doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: http://www.elettra.eu/oasys.html")
