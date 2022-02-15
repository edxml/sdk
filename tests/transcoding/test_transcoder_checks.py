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

import pytest


def test_spurious_post_processor_exception(transcoder):
    type(transcoder).TYPES = ['event-type.a']
    type(transcoder).TYPE_PROPERTIES = {'event-type.a': {'property-a': 'object-type.string'}}
    type(transcoder).TYPE_PROPERTY_POST_PROCESSORS = {'event-type.a': {'spurious': lambda x: [x]}}
    with pytest.raises(ValueError, match='not in TYPE_PROPERTIES'):
        transcoder.generate_ontology()


def test_spurious_type_auto_normalize_properties_exception(transcoder):
    type(transcoder).TYPE_AUTO_REPAIR_NORMALIZE = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        transcoder.generate_ontology()


def test_spurious_type_auto_drop_properties_exception(transcoder):
    type(transcoder).TYPE_AUTO_REPAIR_DROP = {'spurious': []}
    with pytest.raises(ValueError, match='not in the TYPES attribute'):
        transcoder.generate_ontology()
