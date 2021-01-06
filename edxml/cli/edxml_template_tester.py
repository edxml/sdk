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

#  This script can be used to test EDXML templates (story / summary). Among other things,
#  it can generate progressively degraded templates by omitting combinations of event
#  properties. This allows evaluating if the template degrades as intended for events that
#  are missing particular information.

import argparse
import sys

from edxml import Template
from edxml.cli import configure_logger
from edxml.parser import EDXMLOntologyPullParser


def parse_args():
    parser = argparse.ArgumentParser(
        description="This script can be used to test EDXML templates (story / summary). Among other things, "
                    "it can generate progressively degraded templates by omitting combinations of event "
                    "properties. This allows evaluating if the template degrades as intended for events that "
                    "are missing particular information."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        'event_type',
        type=str,
        help='The name of the event type from which the template should be used.'
    )

    parser.add_argument(
        '-c',
        '--colored',
        action='store_true',
        help='Produce colored output, highlighting object values.'
    )

    parser.add_argument(
        '-s',
        '--short',
        action='store_true',
        help='By default, the event story is rendered. This option switches to shorter summary rendering.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    return parser.parse_args()


def main():

    args = parse_args()

    configure_logger(args)

    input = open(args.file, 'rb') if args.file else sys.stdin.buffer

    with EDXMLOntologyPullParser() as ontology_parser:
        ontology_parser.parse(input)
        event_type = ontology_parser.get_ontology().get_event_type(args.event_type)
        if args.short:
            template = event_type.get_summary_template()
        else:
            template = event_type.get_story_template()
            template_properties = Template(template).get_property_names()
            for property_name in event_type.get_properties().keys():
                if property_name not in template_properties:
                    print(f"Warning: property {property_name} is missing in template.")
        for omitted_properties, evaluated in Template.generate_collapsed_templates(
                event_type, template, colorize=args.colored):
            if len(omitted_properties) == 0:
                print('Evaluated with all properties present:')
            else:
                print('Evaluated again after omitting ' + ', '.join(omitted_properties) + ':')
            print('"' + evaluated + '"\n')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
