#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                          Relative EDXML Validator
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
#
#  Python script that checks if the ontologies in de <ontology>
#  sections in all specified EDXML files are compatible.
import argparse
import sys

from edxml.EDXMLBase import EDXMLError
from edxml.EDXMLParser import EDXMLOntologyPullParser, ProcessingInterrupted


def main():
    argparser = argparse.ArgumentParser(
        description="This utility checks if the ontologies contained in all specified EDXML files are mutually "
                    "compatible or not. Only files that have compatible ontologies can be merged. If all files "
                    "prove compatible, the exit status is zero."
    )

    argparser.add_argument(
        '-f',
        '--file',
        type=str,
        action='append',
        help='The name of an EDXML file.'
    )

    args = argparser.parse_args()

    if not args.file or len(args.file) < 2:
        argparser.error('You must specify at least two files.')

    all_compatible = True

    with EDXMLOntologyPullParser() as parser:
        for file_name in args.file:
            print("Checking %s" % file_name)

            try:
                parser.parse(open(file_name))
                break
            except ProcessingInterrupted:
                pass
            except KeyboardInterrupt:
                sys.exit()
            except EDXMLError as error:
                all_compatible = False
                print("EDXML file %s is incompatible with previous files:\n%s" % (file_name, unicode(error)))
            except Exception:
                raise

    if all_compatible:
        print("Files are compatible.")
    else:
        sys.exit(255)


if __name__ == "__main__":
    main()
