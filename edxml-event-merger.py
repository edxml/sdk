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
import argparse
import sys
import time
from typing import Dict, List

from edxml import EDXMLEvent
from edxml.EDXMLFilter import EDXMLPullFilter, EDXMLPushFilter
from edxml.error import EDXMLValidationError


class EDXMLEventMerger(EDXMLPullFilter):

    def __init__(self):

        super(EDXMLEventMerger, self).__init__(sys.stdout.buffer)
        self.HashBuffer = {}

    def _parsed_event(self, event):

        event_hash = event.compute_sticky_hash(self.get_ontology())

        if event_hash in self.HashBuffer:
            event.merge_with([self.HashBuffer[event_hash]], self.get_ontology())

        self.HashBuffer[event_hash] = event

        EDXMLPullFilter._parsed_event(self, event)


class BufferingEDXMLEventMerger(EDXMLPushFilter):

    def __init__(self, event_buffer_size, latency):

        super(BufferingEDXMLEventMerger, self).__init__(sys.stdout.buffer)
        self.__buffer_size = 0
        self.__max_latency = latency
        self.__max_buffer_size = event_buffer_size
        self.__last_output_time = time.time()
        self.__hash_buffer = {}  # type: Dict[str, List[EDXMLEvent]]

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
        for event_hash, events in self.__hash_buffer.items():
            if len(events) > 1:
                output_event = events.pop()
                output_event.merge_with(events, self.get_ontology())
                self._writer.add_event(output_event)

        self.__buffer_size = 0
        self.__last_output_time = time.time()
        self.Buffer = {}


def main():
    parser = argparse.ArgumentParser(
        description='This utility reads an EDXML stream from standard input or from a file and outputs '
                    'that same stream after resolving event hash collisions in the input.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Reads specified EDXML file as input. When this argument is omitted, input will be read '
             'from standard input.'
    )

    parser.add_argument(
        '-l',
        '--max-latency',
        type=float,
        help='When input events are buffered, input event streams having low '
             'event throughput may result in output streams that stay silent '
             'for a long time. Setting this option to a number of (fractional) '
             'seconds, the output latency can be controlled, forcing it to '
             'flush its buffer at regular intervals.'
    )

    parser.add_argument(
        '-b',
        '--buffer',
        type=int,
        help='By default, input events are not buffered, which means that '
             'every input event is either passed through unmodified or '
             'results in a merged version of input event. By setting this '
             'option to a positive integer, the specified number of input '
             'events will be buffed and merged when the buffer is full. That '
             'means that, depending on the buffer size, the number of output '
             'events may be significantly reduced.'
    )

    args = parser.parse_args()

    if not args.file:
        args.file = sys.stdin.buffer
    else:
        args.file = open(args.file, 'rb')

    if args.buffer and args.buffer > 1:
        # We need to read input with minimal
        # input buffering. This works best
        # when using the readline() method.
        with BufferingEDXMLEventMerger(args.buffer, args.max_latency) as merger:
            try:
                while 1:
                    line = args.file.readline()
                    if not line:
                        break
                    merger.feed(line)
            except KeyboardInterrupt:
                sys.exit()
    else:
        with EDXMLEventMerger() as merger:
            try:
                merger.parse(args.file)
            except KeyboardInterrupt:
                sys.exit()
            except EDXMLValidationError as e:
                # The string representations of exceptions do not
                # interpret newlines. As validation exceptions
                # may contain pretty printed XML snippets, this
                # does not yield readable exception messages.
                # So, we only print the message passed to the
                # constructor of the exception.
                print(e.args[0])


if __name__ == "__main__":
    main()
