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

"""
Test to verify that internal references to event types inside properties,
concept associations and attachments remain consistent while performing
ontology upgrades.
"""

from edxml.ontology import Ontology, EventType


def test_property_reference_bookkeeping():

    o1 = Ontology()
    o1.create_object_type('a')

    a = EventType(o1, 'a')
    a.create_property('a', 'a')
    o1._add_event_type(a)

    # Now we create the same event type again. This
    # instance is an update of the previous one.
    a2 = EventType(o1, 'a').set_version(2)
    a2.create_property('a', 'a')
    a2.create_property('b', 'a').make_optional()

    # We add the event type update to the ontology
    # which will update its internal copy. Because
    # sub-objects like properties contain a reference
    # to the event type that contains it the ontology
    # must take care to replace these references with
    # references to its own internal instance.
    o1._add_event_type(a2)

    # Now we create another update of the same event
    # type containing an update to one of the two
    # properties. If the references to the event type
    # instances kept inside the properties are both
    # referring to the same correct event type this
    # then adding it to the ontology will keep the
    # entire structure consistent.
    a3 = EventType(o1, 'a').set_version(3)
    a3.create_property('a', 'a')
    a3.create_property('b', 'a', description='different').make_optional()
    o1._add_event_type(a3)

    # Create another ontology o2 which is identical to o1.
    o2 = Ontology()
    o2.create_object_type('a')
    a4 = o2.create_event_type('a').set_version(3)
    a4.create_property('a', 'a')
    a4.create_property('b', 'a', description='different').make_optional()

    # When the internal event type references are inconsistent
    # then the versions of the event types stored in the two
    # properties will also be mutually inconsistent and an
    # equality assertion will fail.
    assert o1 == o2


def test_property_concept_reference_bookkeeping():

    o1 = Ontology()
    o1.create_object_type('a')
    o1.create_concept('a')

    a = EventType(o1, 'a')
    a.create_property('a', 'a')
    o1._add_event_type(a)

    # Now we create the same event type again. This
    # instance is an update of the previous one.
    a2 = EventType(o1, 'a').set_version(2)
    a2.create_property('a', 'a')
    a2.create_property('b', 'a').make_optional().identifies('a', confidence=1)

    # We add the event type update to the ontology
    # which will update its internal copy. Because
    # sub-objects like properties contain a reference
    # to the event type that contains it the ontology
    # must take care to replace these references with
    # references to its own internal instance.
    o1._add_event_type(a2)

    # Now we create another update of the same event
    # type containing an update to one of the two
    # properties. If the references to the event type
    # instances kept inside the properties are both
    # referring to the same correct event type this
    # then adding it to the ontology will keep the
    # entire structure consistent.
    a3 = EventType(o1, 'a').set_version(3)
    a3.create_property('a', 'a')
    a3.create_property('b', 'a').make_optional().identifies('a', confidence=2)
    o1._add_event_type(a3)

    # Create another ontology o2 which is identical to o1.
    o2 = Ontology()
    o2.create_object_type('a')
    o2.create_concept('a')
    a4 = o2.create_event_type('a').set_version(3)
    a4.create_property('a', 'a')
    a4.create_property('b', 'a').make_optional().identifies('a', confidence=2)

    # When the internal event type references are inconsistent
    # then the versions of the event types stored in the two
    # properties will also be mutually inconsistent and an
    # equality assertion will fail.
    assert o1 == o2


def test_attachment_reference_bookkeeping():

    o1 = Ontology()
    o1.create_object_type('a')

    a = EventType(o1, 'a')
    a.create_attachment('a')
    o1._add_event_type(a)

    # Now we create the same event type again. This
    # instance is an update of the previous one.
    a2 = EventType(o1, 'a').set_version(2)
    a2.create_attachment('a')
    a2.create_attachment('b')

    # We add the event type update to the ontology
    # which will update its internal copy. Because
    # sub-objects like properties contain a reference
    # to the event type that contains it the ontology
    # must take care to replace these references with
    # references to its own internal instance.
    o1._add_event_type(a2)

    # Now we create another update of the same event
    # type containing an update to one of the two
    # properties. If the references to the event type
    # instances kept inside the properties are both
    # referring to the same correct event type this
    # then adding it to the ontology will keep the
    # entire structure consistent.
    a3 = EventType(o1, 'a').set_version(3)
    a3.create_attachment('a')
    a3.create_attachment('b').set_description('changed')
    o1._add_event_type(a3)

    # Create another ontology o2 which is identical to o1.
    o2 = Ontology()
    o2.create_object_type('a')
    a4 = o2.create_event_type('a').set_version(3)
    a4.create_attachment('a')
    a4.create_attachment('b').set_description('changed')

    # When the internal event type references are inconsistent
    # then the versions of the event types stored in the two
    # properties will also be mutually inconsistent and an
    # equality assertion will fail.
    assert o1 == o2
