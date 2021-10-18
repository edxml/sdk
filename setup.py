# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
# with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
#  long_description = f.read()

# Explicitly state a version to please flake8
__version__ = 1.0
# This will read __version__ from edxml/version.py
exec(compile(open('edxml/version.py', "rb").read(), 'edxml/version.py', 'exec'))

setup(
    name='edxml',
    version=__version__,

    # A description of your project
    description='The EDXML Software Development Kit',
    long_description='Python implementation of the EDXML specification and tools for application development',

    # The project's main homepage
    url='https://github.com/edxml/sdk',

    # Author details
    author='Dik Takken',
    author_email='dik.takken@edxml.org',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3'
    ],

    # What does your project relate to?
    keywords='edxml sdk xml',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=[]),

    # If there are data files included in your packages that need to be
    # installed, specify them here. If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'edxml': ['**/*.pyi']
    },

    # Add entry points which will be installed as CLI utilities
    entry_points={
        'console_scripts': [
            'edxml-cat=edxml.cli.edxml_cat:main',
            'edxml-ddgen=edxml.cli.edxml_ddgen:main',
            'edxml-diff=edxml.cli.edxml_diff:main',
            'edxml-filter=edxml.cli.edxml_filter:main',
            'edxml-hash=edxml.cli.edxml_hash:main',
            'edxml-merge=edxml.cli.edxml_merge:main',
            'edxml-replay=edxml.cli.edxml_replay:main',
            'edxml-stats=edxml.cli.edxml_stats:main',
            'edxml-to-csv=edxml.cli.edxml_to_csv:main',
            'edxml-to-text=edxml.cli.edxml_to_text:main',
            'edxml-validate=edxml.cli.edxml_validate:main',
            'edxml-mine=edxml.cli.edxml_mine:main',
            'edxml-template-tester=edxml.cli.edxml_template_tester:main',
        ],
    },

    # List run-time dependencies here. These will be installed by pip when your
    # project is installed.
    # See https://pip.pypa.io/en/latest/reference/pip_install.html#requirements-file-format
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=['lxml>=3.8', 'python-dateutil', 'edxml-schema==3.0.0.dev3',
                      'iso3166', 'pytz', 'termcolor', 'graphviz', 'typing', 'pytest',
                      'ipy', 'coverage', 'edxml-test-corpus==3.0.0.dev4'],

    # Specify additional packages that are only installed for specific purposes,
    # like building documentation.
    extras_require={
        'doc': [
            'sphinx',
            'sphinxcontrib-napoleon'
        ]
    }
)
