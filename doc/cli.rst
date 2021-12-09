.. highlight:: shell

Command Line Utilities
======================

The EDXML SDK includes various command line utilities to process EDXML data and to aid in application development. Most utilities take EDXML data from standard input, write to standard output and process the data in a streaming fashion.

edxml-cat
---------

This utility concatenates two or more EDXML files resulting in one output file. It will fail when the specified EDXML files are invalid or mutually incompatible. Example::

  edxml-cat -f one.edxml -f another.edxml > combined.edxml


edxml-ddgen
-----------

This is a dummy data generator which can output random EDXML data streams. It is mostly used for testing processing performance of EDXML applications. Example::

  edxml-ddgen --limit 1000

edxml-diff
----------

Computes the semantic difference between two EDXML data files, outputting the differences on standard output. This means that it will only consider differences that are significant. For example, the order of the events in an EDXML document has no significance. Exit status is zero when the data files are semantically identical. Example::

  edxml-diff -f one.edxml -f another.edxml

edxml-filter
------------

This utility reads an EDXML stream from standard input and filters it according to the user supplied parameters. The result is sent to standard output. Example::

  edxml-filter -f data.edxml --source-uri '/acme/offices/berlin/*'

edxml-hash
----------

This utility outputs sticky hashes for every event in a given EDXML file or input stream. The hashes are printed to standard output. Example::

  edxml-hash -f data.edxml

edxml-merge
-----------

This utility reads an EDXML stream from standard input or from a file and outputs that same stream after resolving event hash collisions in the input. Example::

  edxml-merge -f data.edxml

edxml-mine
----------

This utility performs concept mining on EDXML data received on standard input or from a file. It can output the results as JSON, as a visualization or in plain English. Example::

  edxml-mine -f data.edxml --dump-json

edxml-replay
------------

This utility accepts EDXML data as input and writes time shifted events to standard output. Timestamps of input events are shifted to the current time. This is useful for simulating live EDXML data sources using previously recorded data. Note that the script assumes that the events in the input stream are time ordered. Example::

  edxml-replay -f data.edxml --speed 2

edxml-stats
-----------

This utility prints various statistics for one or more EDXML input files. Example::

  edxml-stats -f data.edxml --count

edxml-template-tester
---------------------

This script can be used to test EDXML templates (story / summary). Among other things, it can generate progressively degraded evaluated templates by omitting combinations of event properties. This allows evaluating if the template degrades as intended for events that are missing particular information. Example::

  edxml-template-tester some.event.type.name -f data.edxml

edxml-to-delimited
------------------

This utility accepts EDXML data as input and writes the events to standard output, formatted in rows and columns. For every event property, a output column is generated. If one property has multiple objects, multiple output lines are generated. Example::

  edxml-to-delimited -f data.edxml --properties property,another-property

edxml-to-text
-------------

This utility outputs evaluated event story or summary templates for every event in a given EDXML file or input stream. The strings are printed to standard output. Example::

  edxml-to-text -f data.edxml

edxml-validate
--------------

This utility checks EDXML data against the specification requirements. Its exit status will be zero if the provided data is valid EDXML. Example::

  edxml-validate -f data.edxml

