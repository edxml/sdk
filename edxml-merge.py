#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                          EDXML Merging Utility
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
#  This utility reads multiple compatible EDXML files and merges them into
#  one new EDXML file, which is then printed on standard output.

import argparse
import logging
import sys

from edxml.error import EDXMLValidationError
from edxml.EDXMLFilter import EDXMLPullFilter
from edxml.logger import log


class EDXMLMerger(EDXMLPullFilter):
    def __init__(self):
        super().__init__(sys.stdout.buffer)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._writer.close()

    def parse(self, input_file, foreign_element_tags=()):
        super().parse(input_file, foreign_element_tags)
        self.close()

    def _close(self):
        # We suppress closing the output writer, allowing
        # us to parse multiple files in succession.
        ...


parser = argparse.ArgumentParser(
    description='This utility merges two or more EDXML files into one.'
)

parser.add_argument(
    '-f',
    '--file',
    type=str,
    action='append',
    help='A file name to be used as input for the merge operation.'
)

parser.add_argument(
    '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
)

parser.add_argument(
    '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
)


def main():
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

    if args.file is None or len(args.file) < 2:
        sys.stderr.write("Please specify at least two EDXML files for merging.\n")
        sys.exit()

    with EDXMLMerger() as merger:
        for file_name in args.file:
            log.info("\nMerging file %s:" % file_name)
            try:
                merger.parse(file_name)
            except KeyboardInterrupt:
                pass
            except EDXMLValidationError as exception:
                exception.message = "EDXML file %s is incompatible with previous files: %s" % (file_name, exception)
                raise
            except Exception:
                raise


if __name__ == "__main__":
    main()
