#!/usr/bin/env python3

# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

#  This script reads an EDXML stream from standard input or from a file and outputs
#  that same stream after resolving event hash collisions in the input. Every time an
#  input event collides with a preceding event, the event will be merged and an updated
#  version is output. That means that the number of output events equals the number of
#  input events.
#
#  Note that, unless buffering is used, this script needs to store one event for each
#  sticky hash of the input events in RAM. For large event streams that contain events
#  with many sticky hashes, it will eventually run out of memory.

import argparse
import sys
import time
from typing import Dict, List

from edxml import EDXMLEvent
from edxml.cli import configure_logger
from edxml.filter import EDXMLPullFilter, EDXMLPushFilter
from edxml.error import EDXMLValidationError
from edxml.logger import log


class EDXMLEventMerger(EDXMLPullFilter):

    def __init__(self):
        super().__init__(sys.stdout.buffer)
        self.hash_buffer = {}
        self.num_merged = 0
        self.num_processed = 0

    def _parsed_event(self, event):
        event_type = self.get_ontology().get_event_type(event.get_type_name())
        event_hash = event.compute_sticky_hash(event_type)

        if event_hash in self.hash_buffer:
            event_type = self.get_ontology().get_event_type(event.get_type_name())
            event = event_type.merge_events([self.hash_buffer[event_hash], event])
            self.num_merged += 1

        # Note that we copy the event here. The reason for doing
        # this is that the parser will dereference the event after
        # this method exits. As a result, each event will have
        # its own explicit namespace. Storing a copy prevents this.
        self.hash_buffer[event_hash] = event.copy()

        self.num_processed += 1

    def _close(self):
        for event_hash, event in self.hash_buffer.items():
            EDXMLPullFilter._parsed_event(self, event)
        super()._close()
        log.info(f"Processed {self.num_processed} events, merged {self.num_merged}.")


class BufferingEDXMLEventMerger(EDXMLPushFilter):

    def __init__(self, event_buffer_size, latency):

        super().__init__(output=sys.stdout.buffer)
        self.__buffer_size = 0
        self.__max_latency = latency
        self.__max_buffer_size = event_buffer_size
        self.__last_output_time = time.time()
        self.__hash_buffer = {}  # type: Dict[str, List[EDXMLEvent]]
        self.__num_merged = 0
        self.__num_processed = 0

    def _parsed_event(self, event):
        event_type = self.get_ontology().get_event_type(event.get_type_name())
        event_hash = event.compute_sticky_hash(event_type)

        # Note that we copy the event here. The reason for doing
        # that is that the parser will dereference the event after
        # this method exists. As a result, each event will have
        # its own explicit namespace. Storing a copy prevents this.
        event = event.copy()

        if event_hash in self.__hash_buffer:
            # This hash is in our buffer, which means
            # we have a collision. Add the event for
            # merging later.
            self.__hash_buffer[event_hash].append(event)
            self.__num_merged += 1
        else:
            # We have a new hash, add it to
            # the buffer.
            self.__hash_buffer[event_hash] = [event]

        self.__num_processed += 1
        self.__buffer_size += 1
        if self.__buffer_size >= self.__max_buffer_size:
            self._flush_buffer()

        if self.__buffer_size > 0 and 0 < self.__max_latency <= (time.time() - self.__last_output_time):
            self._flush_buffer()

    def _flush_buffer(self):
        for event_hash, events in self.__hash_buffer.items():
            if len(events) > 0:
                if len(events) > 1:
                    output_event = self.get_ontology().get_event_type(events[0].get_type_name()).merge_events(events)
                else:
                    output_event = events[0]
                self._writer.add_event(output_event)

        self.__buffer_size = 0
        self.__last_output_time = time.time()
        self.__hash_buffer = {}

    def _close(self):
        super()._close()
        log.info(f"Processed {self.__num_processed} events, merged {self.__num_merged}.")


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

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    if not args.file:
        args.file = sys.stdin.buffer
    else:
        args.file = open(args.file, 'rb')

    if args.buffer and args.buffer > 1:
        # We need to read input with minimal
        # input buffering. This works best
        # when using the readline() method.
        with BufferingEDXMLEventMerger(args.buffer, args.max_latency) as merger:
            while True:
                line = args.file.readline()
                if not line:
                    break
                merger.feed(line)
    else:
        with EDXMLEventMerger() as merger:
            merger.parse(args.file)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(1)
    except EDXMLValidationError as e:
        # The string representations of exceptions do not
        # interpret newlines. As validation exceptions
        # may contain pretty printed XML snippets, this
        # does not yield readable exception messages.
        # So, we only print the message passed to the
        # constructor of the exception.
        sys.stderr.write(e.args[0])
