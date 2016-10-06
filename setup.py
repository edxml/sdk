from setuptools import setup, find_packages # Always prefer setuptools over distutils
from codecs import open # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
#with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
#  long_description = f.read()

exec(open('edxml/version.py').read())

setup(
  name = 'edxml',
  version = __version__,

  # A description of your project
  description = 'The EDXML Software Developers Kit',
  long_description = 'Python classes and example applications for use with the EDXML specification at edxml.org',

  # The project's main homepage
  url = 'https://github.com/dtakken/edxml-sdk',

  # Author details
  author = 'Dik Takken',
  author_email = 'd.h.j.takken@xs4all.nl',

  # Choose your license
  license='LGPL',

  # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
  classifiers = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 5 - Production/Stable',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Libraries :: Python Modules',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2'
  ],

  # What does your project relate to?
  keywords = 'edxml sdk xml',

  # You can just specify the packages manually here if your project is
  # simple. Or you can use find_packages().
  packages = find_packages(exclude=[]),

  # If there are data files included in your packages that need to be
  # installed, specify them here. If using Python 2.6 or less, then these
  # have to be included in MANIFEST.in as well.
  package_data={
  'edxml': ['schema/edxml-schema-2.1.0.rng'],
  },

  # List run-time dependencies here. These will be installed by pip when your
  # project is installed. 
  # See https://pip.pypa.io/en/latest/reference/pip_install.html#requirements-file-format
  # For an analysis of "install_requires" vs pip's requirements files see:
  # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
  install_requires = ['lxml>=3.4', 'python-dateutil', 'iso3166', 'pytz', 'termcolor'],

  # If elementtree is available, it can be used for generating EDXML definitions
  # in stead of using SAX XMLGenerator.
  extras_require = {
    'ElementTree':  ['elementtree']
  }
)
