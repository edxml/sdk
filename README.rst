EDXML SDK
=========

|license| |tests| |docs| |coverage| |pyversion|

.. |license| image::  https://img.shields.io/badge/License-MIT-blue.svg
.. |tests| image::    https://github.com/edxml/sdk/workflows/tests/badge.svg
.. |docs| image::     https://readthedocs.org/projects/edxml-sdk/badge/?version=master
.. |coverage| image:: https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/dtakken/35971300c60a5a54c91084fc80da9b49/raw/covbadge.json
.. |pyversion| image::  https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue

EDXML_ is a data representation that transforms arbitrary data records into stories
that machines can read and understand. Computers can read EDXML documents similar to
how humans read a novel. This enables computers to actively assist human analysts
in making sense of data, correlate data from multiple sources and connect the dots.

This repository contains the **EDXML Software Development Kit (SDK)**. The
SDK features the edxml Python package, which contains an implementation of the
`EDXML specification <http://edxml.org/spec>`_. It also offers some command line
tools to inspect EDXML documents and aid in application development.

The package can be installed using Pip::

    pip install edxml

* `Documentation <http://edxml-sdk.readthedocs.org/>`_ (Read the Docs)
* `Installer <http://pypi.python.org/pypi/edxml/>`_ (PyPI)
* `Source code <https://github.com/edxml/sdk>`_ (Github)

.. _EDXML: http://edxml.org/
