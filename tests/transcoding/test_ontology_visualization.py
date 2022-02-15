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

from io import BytesIO

from edxml.transcode import TranscoderMediator, RecordTranscoder


def test_ontology_concept_visualization():
    class TestTranscoder(RecordTranscoder):
        """
        This extension of RecordTranscoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        RecordTranscoder class would cause side effects because that class is
        shared by all tests.
        """

        @classmethod
        def create_event_type(cls, event_type_name, ontology):
            event_type = super().create_event_type(event_type_name, ontology)
            if event_type_name == 'event-type.a':
                event_type.get_properties()['property-a'].relate_intra('related to', 'property-b')
            else:
                event_type.get_properties()['property-a'].relate_inter('related to', 'property-b')

        def create_object_types(self, ontology):
            ontology.create_object_type('object-type-string')

        def create_concepts(self, ontology):
            ontology.create_concept('concept-a')

    # Below we define two event types each having two properties. The properties are
    # associated with concepts. The event types share a common object type, which means that both
    # event types will be interconnected by a common object type node.

    TestTranscoder.TYPES = ['event-type.a', 'event-type.b']
    TestTranscoder.TYPE_MAP = {'selector a': 'event-type.a', 'selector b': 'event-type.b'}
    TestTranscoder.TYPE_PROPERTIES = {
        'event-type.a': {'property-a': 'object-type-string', 'property-b': 'object-type-string'},
        'event-type.b': {'property-a': 'object-type-string', 'property-b': 'object-type-string'}
    }
    TestTranscoder.TYPE_PROPERTY_CONCEPTS = {
        'event-type.a': {'property-a': {'concept-a': 1}, 'property-b': {'concept-a': 9}},
        'event-type.b': {'property-a': {'concept-a': 1}, 'property-b': {'concept-a': 9}}
    }
    TestTranscoder.TYPE_PROPERTY_CONCEPTS_CNP = {
        'event-type.a': {'property-a': {'concept-a': 0}},
        'event-type.b': {'property-a': {'concept-a': 0}}
    }
    TestTranscoder.TYPE_PROPERTY_ATTRIBUTES = {
        'event-type.a': {'property-a': {'concept-a': ['object-type-string:attr', 'attr-s', 'attr-p']}},
        'event-type.b': {'property-a': {'concept-a': ['object-type-string:attr', 'attr-s', 'attr-p']}}
    }

    mediator = TranscoderMediator(BytesIO())
    mediator.register('records', TestTranscoder())

    # Generate graph and fetch its source text
    lines = mediator.generate_graphviz_concept_relations().source.splitlines()

    # There should be a common object type node
    assert count_lines_containing(lines, 'label="object-type-string"')

    # All event properties should be linked to a common object type node
    assert count_lines_containing(lines, 'event-type.a_property-a', '->', 'object-type-string')
    assert count_lines_containing(lines, 'event-type.a_property-b', '->', 'object-type-string')
    assert count_lines_containing(lines, 'event-type.b_property-a', '->', 'object-type-string')
    assert count_lines_containing(lines, 'event-type.b_property-b', '->', 'object-type-string')

    # The relations between both property pairs should be shown, each consisting of two
    # edges property -> label -> property
    assert count_lines_containing(lines, 'event-type.a_property-a', '->', 'label_', 'event-type.a_property-b') == 2
    assert count_lines_containing(lines, 'event-type.b_property-a', '->', 'label_', 'event-type.b_property-b') == 2

    # The two inter-concept relations should be shown using dashed edges
    assert count_lines_containing(lines, '->', 'style=dashed') == 2

    # The attribute nodes should indicate their concept confidence by means of background color
    assert count_lines_containing(lines, 'property-a', 'BGCOLOR="red2"') == 2
    assert count_lines_containing(lines, 'property-b', 'BGCOLOR="forestgreen"') == 2


def count_lines_containing(lines, *phrases):
    matches = []
    for line in lines:
        if tuple(phrase for phrase in phrases if phrase in line) != phrases:
            continue
        matches.append(line)
    return len(matches)
