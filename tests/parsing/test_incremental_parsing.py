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
import os

from edxml import EDXMLPushParser


def test_parse():
    # This test feeds an EDXML file to the parser, one character at a time. We do that
    # to make sure that the parser does not fail when dealing with partially read EDXML input.
    with EDXMLPushParser() as parser:
        for line in open(os.path.dirname(__file__) + '/input.edxml').readlines():
            for character in line:
                parser.feed(character)
