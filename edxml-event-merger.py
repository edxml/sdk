#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                            EDXML Event Merger
#
#                            EXAMPLE APPLICATION
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
#                          (d.h.j.takken@xs4all.nl)
#
#          This file is part of the EDXML Software Development Kit (SDK).
#
#
#  The EDXML SDK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The EDXML SDK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with the EDXML SDK.  If not, see <http://www.gnu.org/licenses/>.
#
#
#  ===========================================================================
#
#  This script reads an EDXML stream from standard input or from a file and outputs
#  that same stream after resolving event hash collisions in the input. Every time an
#  input event collides with a preceding event, the event will be merged and an updated
#  version is output. That means that the number of output events equals the number of
#  input events.
#
#  Note that, unless buffering is used, this script needs to store one event for each
#  sticky hash of the input events in RAM. For large event streams that contain events
#  with many different sticky hashes, it will eventually run out of memory. Extending
#  this example to use an external storage backend in order to overcome this limitation
#  is left as an exercise to the user.

import sys
import time
from edxml.EDXMLFilter import EDXMLPullFilter, EDXMLPushFilter


class EDXMLEventMerger(EDXMLPullFilter):

    def __init__(self):

        super(EDXMLEventMerger, self).__init__(sys.stdout)
        self.HashBuffer = {}

    def _parsed_event(self, event):

        event_hash = event.compute_sticky_hash(self.get_ontology())

        if event_hash in self.HashBuffer:
            event.merge_with([self.HashBuffer[event_hash]], self.get_ontology())

        self.HashBuffer[event_hash] = event

        EDXMLPullFilter._parsed_event(self, event)


class BufferingEDXMLEventMerger(EDXMLPushFilter):

    def __init__(self, event_buffer_size, latency):

        super(BufferingEDXMLEventMerger, self).__init__(sys.stdout)
        self.__buffer_size = 0
        self.__max_latency = latency
        self.__max_buffer_size = event_buffer_size
        self.__last_output_time = time.time()
        self.__hash_buffer = {}

    def _close_event_group(self, event_type_name, event_source_id):

        self._flush_buffer()

        EDXMLPushFilter._close_event_group(self, event_type_name, event_source_id)

    def _parsed_event(self, event):

        event_hash = event.compute_sticky_hash(self.get_ontology())

        if event_hash in self.__hash_buffer:
            # This hash is in our buffer, which means
            # we have a collision. Add the event for
            # merging later.
            self.__hash_buffer[event_hash].append(event)
        else:
            # We have a new hash, add it to
            # the buffer.
            self.__hash_buffer[event_hash] = [event]

        self.__buffer_size += 1
        if self.__buffer_size >= self.__max_buffer_size:
            self._flush_buffer()

        if self.__buffer_size > 0 and 0 < self.__max_latency <= (time.time() - self.__last_output_time):
            self._flush_buffer()

    def _flush_buffer(self):
        for event_hash, events in self.__hash_buffer.iteritems():
            if len(events) > 1:
                output_event = events.pop()
                output_event.merge_with(events, self.get_ontology())
                self._writer.add_event(output_event)

        self.__buffer_size = 0
        self.__last_output_time = time.time()
        self.Buffer = {}


def print_help():

    print("""

   This utility reads an EDXML stream from standard input or from a file and outputs
   that same stream after resolving event hash collisions in the input.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

     -b                By default, input events are not buffered, which means that
                       every input event is either passed through unmodified or
                       results in a merged version of input event. By setting this
                       option to a positive integer, the specified number of input
                       events will be buffed and merged when the buffer is full. That
                       means that, depending on the buffer size, the number of output
                       events may be significantly reduced.

     -l                When input events are buffered, input event streams having low
                       event throughput may result in output streams that stay silent
                       for a long time. Setting this option to a number of (fractional)
                       seconds, the output latency can be controlled, forcing it to
                       flush its buffer at regular intervals.
   Example:

     edxml-event-merger.py -b 1000 -l 10 -f input.edxml > output.edxml

""")


curr_option = 1
buffer_size = 1
output_latency = 0
input_file_name = None

while curr_option < len(sys.argv):

    if sys.argv[curr_option] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[curr_option] == '-f':
        curr_option += 1
        input_file_name = sys.argv[curr_option]

    elif sys.argv[curr_option] == '-b':
        curr_option += 1
        buffer_size = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '-l':
        curr_option += 1
        output_latency = float(sys.argv[curr_option])

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[curr_option])
        sys.exit()

    curr_option += 1

if input_file_name is None:
    sys.stderr.write(
        "\nNo filename was given, waiting for EDXML data on STDIN...(use --help to get help)")
    event_input = sys.stdin
else:
    sys.stderr.write("\nProcessing file %s:" % input_file_name)
    event_input = open(input_file_name)

sys.stdout.flush()

if buffer_size > 1:
    # We need to read input with minimal
    # input buffering. This works best
    # when using the readline() method.
    with BufferingEDXMLEventMerger(buffer_size, output_latency) as merger:
        try:
            while 1:
                Line = event_input.readline()
                if not Line:
                    break
                merger.feed(Line)
        except KeyboardInterrupt:
            sys.exit()
else:
    with EDXMLEventMerger() as merger:
        try:
            merger.parse(open('demo.edxml'))
        except KeyboardInterrupt:
            sys.exit()
