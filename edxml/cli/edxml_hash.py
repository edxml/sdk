#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                        EDXML Sticky Hash Calculator
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
#
#  This script outputs sticky hashes for every event in a given
#  EDXML file or input stream. The hashes are printed to standard output.
import argparse
import logging
import sys
from edxml.EDXMLParser import EDXMLPullParser


class EDXMLEventHasher(EDXMLPullParser):

    def _parsed_event(self, event):
        event_type = self.get_ontology().get_event_type(event.get_type_name())
        print(event.compute_sticky_hash(event_type))


def main():
    parser = argparse.ArgumentParser(
        description='This utility outputs sticky hashes for every event in a given '
                    'EDXML file or input stream. The hashes are printed to standard output.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.ERROR)
    elif args.verbose:
        if args.verbose > 0:
            logger.setLevel(logging.INFO)
        if args.verbose > 1:
            logger.setLevel(logging.DEBUG)

    event_input = args.file or sys.stdin.buffer

    try:
        EDXMLEventHasher().parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
