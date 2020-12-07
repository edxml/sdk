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

#  This utility reads multiple compatible EDXML files and merges them into
#  one new EDXML file, which is then printed on standard output.

import argparse
import sys

from edxml.cli import configure_logger
from edxml.error import EDXMLValidationError
from edxml.filter import EDXMLPullFilter
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


def parse_args():
    parser = argparse.ArgumentParser(
        description='This utility concatenates two or more EDXML files resulting in one output file.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        action='append',
        help='A file name to be used as input.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    if args.file is None or len(args.file) < 2:
        parser.error("Please specify at least two EDXML files for merging.")
        sys.exit()

    return args


def main():
    args = parse_args()

    configure_logger(args)

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
