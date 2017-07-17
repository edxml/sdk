.. EDXML SDK documentation master file, created by
   sphinx-quickstart on Fri Dec  5 15:27:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The edxml Python package
========================

This site documents the edxml Python package, which is part of the `EDXML Software Developers Kit <https://github.com/dtakken/edxml-sdk/>`_. This package offers a reference implementation of the `EDXML specification <http://edxml.org/>`_ as well as classes for generating, validating and processing of EDXML data streams.

EDXML is a versatile data representation which facilitates implementing data integration solutions. It joins data with semantics to allow data sources to specify the exact meaning of the data they produce. This yields a data representation that combines a broad representational scope with a simple data structure.

Example applications that use this package can be obtained from `Github <https://github.com/dtakken/edxml-sdk/>`_ while the EDXML Python package itself can be installed using Pip:

::

    pip install edxml

Reference Manual
================

.. toctree::
   :maxdepth: 0

   writing
   reading
   filtering
   ontology
   event

Tutorials
=========

* :doc:`EDXML Data Modeling<tutorial/edxml-modelling>`

EDXML Patterns
==============

* :doc:`Composed Data Sources<patterns/composed-sources>`
* :doc:`Ontology Bricks<patterns/ontology-bricks>`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

