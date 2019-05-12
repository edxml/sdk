#!/usr/bin/env python
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
import sys
from edxml.EDXMLParser import EDXMLPullParser


class EDXMLEventHasher(EDXMLPullParser):

    def _parsed_event(self, event):

        ontology = self.get_ontology()
        print(event.compute_sticky_hash(ontology))


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

    args = parser.parse_args()

    event_input = args.file or sys.stdin.buffer

    try:
        EDXMLEventHasher().parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
