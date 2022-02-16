.. EDXML SDK documentation master file, created by
   sphinx-quickstart on Fri Dec  5 15:27:32 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The edxml Python package
========================

This package offers a Python implementation of the `EDXML specification <http://edxml.org/>`_ and various tools for EDXML application development. It can be installed using Pip:

::

    pip install edxml

Overview
--------

The EDXML SDK can be used for generating and processing EDXML data. Additionally it offers some helpful tools to ease application development and unit testing. For example, it can generate visualizations of your ontology, show you how your EDXML templates will behave and normalize input data. Finally, the SDK contains a basic `concept mining <http://edxml.org/concept-mining/>`_ implementation.

EDXML Data Modelling
--------------------

.. toctree::
   :maxdepth: 1

   edxml-modelling/intro
   edxml-modelling/event-hashes
   edxml-modelling/parents-children

API Documentation
-----------------

.. toctree::
   :maxdepth: 1

   writing
   reading
   filtering
   transcoding
   event
   ontology
   bricks
   event_type_factory
   mining

Command Line Utilities
----------------------

An overview of included command line utilities can be found :doc:`here <cli>`.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`

