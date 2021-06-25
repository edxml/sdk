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

from io import BytesIO
from edxml import EDXMLWriter, EventCollection, EDXMLEvent
from edxml.error import EDXMLEventValidationError, EDXMLOntologyValidationError
from edxml.ontology import Ontology, DataType
from lxml import etree


@pytest.fixture()
def ontology():
    edxml_ontology = Ontology()
    edxml_ontology.create_object_type('string', data_type=DataType.string(length=3, upper_case=False).type)
    edxml_ontology.create_object_type('int', data_type=DataType.int().type)
    event_type = edxml_ontology.create_event_type('ea')
    event_type.create_property('a', object_type_name='string')
    event_type.create_property('b', object_type_name='string').make_optional()
    event_type.create_property('c', object_type_name='int').make_optional()
    event_type.create_attachment('a')
    edxml_ontology.create_event_source('/test/')
    return edxml_ontology


@pytest.fixture()
def invalid_ontology(ontology):
    # An empty story template results in an invalid ontology
    # which is only detected when validated against the RelaxNG
    # schema. As such, it uses a different code path in the writer.
    ontology.get_event_type('ea').set_story_template('')
    return ontology


@pytest.fixture()
def event():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='ea',
        source_uri='/test/'
    )


@pytest.fixture()
def event_unknown_type():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='unknown',
        source_uri='/test/'
    )


@pytest.fixture()
def event_unknown_source():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='ea',
        source_uri='/unknown/'
    )


@pytest.fixture()
def event_unknown_attachment():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='ea',
        source_uri='/test/'
    ).set_attachment('unknown', 'test')


@pytest.fixture()
def event_without_type():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        source_uri='/test/'
    )


@pytest.fixture()
def event_without_source():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='ea'
    )


@pytest.fixture()
def event_invalid_object():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'BAR'},
        event_type_name='ea',
        source_uri='/test/'
    )


@pytest.fixture()
def event_invalid_object_beyond_repair():
    return EDXMLEvent(
        properties={'a': 'foo', 'b': 'barr'},
        event_type_name='ea',
        source_uri='/test/'
    )


@pytest.fixture()
def event_dropped_object():
    return EDXMLEvent(
        properties={'a': 'foo'},
        event_type_name='ea',
        source_uri='/test/'
    )


@pytest.fixture()
def event_obscure_error():
    class WeirdEvent(EDXMLEvent):
        def get_element(self, sort=False):
            return etree.Element('weird')

    return WeirdEvent(
        properties={'a': 'foo', 'b': 'bar'},
        event_type_name='ea',
        source_uri='/test/'
    )


@pytest.fixture()
def foreign_element():
    element = etree.Element('{/test/namespace}test')
    etree.SubElement(element, 'sub')
    return element


def test_write():
    writer = EDXMLWriter(output=None)
    writer.close()
    output = writer.flush()

    assert output == b'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n' \
                     b'<edxml xmlns="http://edxml.org/edxml" version="3.0.0"></edxml>'


def test_write_external_output():
    output = BytesIO()
    EDXMLWriter(output).close()
    output.seek(0)

    assert output.read() == b'<?xml version=\'1.0\' encoding=\'utf-8\'?>\n' \
                            b'<edxml xmlns="http://edxml.org/edxml" version="3.0.0"></edxml>'


def test_write_ontology(ontology):
    with EDXMLWriter(output=None) as writer:
        writer.add_ontology(ontology).close()
        output = writer.flush()

    assert EventCollection.from_edxml(output).ontology == ontology


def test_write_invalid_ontology(invalid_ontology):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLOntologyValidationError):
            writer.add_ontology(invalid_ontology).close()


def test_write_event(ontology, event):
    with EDXMLWriter(output=None) as writer:
        writer.add_ontology(ontology).add_event(event).close()

    events = EventCollection.from_edxml(writer.flush())

    assert len(events) == 1
    assert next(iter(events)) == event


def test_write_event_before_ontology_fails(ontology, event):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError):
            writer.add_event(event).add_ontology(ontology).close()


def test_write_foreign_element(ontology, foreign_element):
    with EDXMLWriter(output=None) as writer:
        writer.add_foreign_element(foreign_element).close()

    events = EventCollection.from_edxml(writer.flush(), foreign_element_tags=['{/test/namespace}test'])

    assert len(events.foreign_elements) == 1


def test_write_pretty_print(ontology, event):
    with EDXMLWriter(output=None, pretty_print=True) as writer:
        writer.add_ontology(ontology).add_event(event).close()
        output = writer.flush()

    assert len(output.splitlines()) == 30


def test_write_no_pretty_print(ontology, event):
    with EDXMLWriter(output=None, pretty_print=False) as writer:
        writer.add_ontology(ontology).add_event(event).close()
        output = writer.flush()

    assert len(output.splitlines()) == 4


def test_write_invalid_event(ontology, event_invalid_object):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='Invalid value for property'):
            writer.add_ontology(ontology).add_event(event_invalid_object).close()


def test_write_invalid_event_ignore(ontology, event_invalid_object):
    with EDXMLWriter(output=None) as writer:
        writer.ignore_invalid_events()
        writer.add_ontology(ontology).add_event(event_invalid_object)

    # Writer should have swallowed the invalid event.
    assert len(EventCollection.from_edxml(writer.flush())) == 0


def test_write_invalid_event_repair_normalize_fail(ontology, event_invalid_object):
    with EDXMLWriter(output=None) as writer:
        # Note: Property 'b' has the invalid object.
        writer.enable_auto_repair_normalize('ea', ['a'])
        with pytest.raises(EDXMLEventValidationError, match='Invalid value for property'):
            writer.add_ontology(ontology).add_event(event_invalid_object).close()


def test_write_invalid_event_repair_normalize_string(ontology, event, event_invalid_object, caplog):
    with EDXMLWriter(output=None) as writer:
        # Note: Property 'b' has the invalid object.
        writer.enable_auto_repair_normalize('ea', ['b'])
        writer.add_ontology(ontology).add_event(event_invalid_object)

    events = EventCollection.from_edxml(writer.flush())

    # Writer should have normalized the invalid event object.
    assert next(iter(events)) == event

    assert '1 out of 1 events were automatically repaired' in ''.join(caplog.messages)


def test_write_invalid_event_repair_normalize_integer(ontology, event, caplog):
    # Note: Property 'c' has data type 'int'
    event.properties['c'] = {1.2}
    with EDXMLWriter(output=None) as writer:
        writer.enable_auto_repair_normalize('ea', ['c'])
        writer.add_ontology(ontology).add_event(event)

    events = EventCollection.from_edxml(writer.flush())

    # Writer should have normalized the invalid event object.
    assert next(iter(events))['c'] == ['1']

    assert '1 out of 1 events were automatically repaired' in ''.join(caplog.messages)


def test_write_invalid_event_repair_drop_fail(ontology, event_invalid_object):
    with EDXMLWriter(output=None) as writer:
        # Note: Property 'b' has the invalid object.
        writer.enable_auto_repair_normalize('ea', ['a'])
        writer.enable_auto_repair_drop('ea', ['a'])
        with pytest.raises(EDXMLEventValidationError, match='Invalid value for property'):
            writer.add_ontology(ontology).add_event(event_invalid_object).close()


def test_write_invalid_event_repair_drop(ontology, event_invalid_object_beyond_repair, event_dropped_object, caplog):
    with EDXMLWriter(output=None) as writer:
        # Note: Property 'b' has the invalid object.
        writer.enable_auto_repair_normalize('ea', ['b'])
        writer.enable_auto_repair_drop('ea', ['b'])
        writer.add_ontology(ontology).add_event(event_invalid_object_beyond_repair)

    events = EventCollection.from_edxml(writer.flush())

    # Writer should have dropped the invalid event object.
    assert next(iter(events)) == event_dropped_object

    assert '1 out of 1 events were automatically repaired' in ''.join(caplog.messages)


def test_write_event_without_type(ontology, event_without_type):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='no event type set'):
            writer.add_ontology(ontology).add_event(event_without_type).close()


def test_write_event_without_source(ontology, event_without_source):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='no event source set'):
            writer.add_ontology(ontology).add_event(event_without_source).close()


def test_write_event_unknown_type(ontology, event_unknown_type):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='unknown event type'):
            writer.add_ontology(ontology).add_event(event_unknown_type).close()


def test_write_event_unknown_source(ontology, event_unknown_source):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='unknown source URI'):
            writer.add_ontology(ontology).add_event(event_unknown_source).close()


def test_write_event_unknown_attachment(ontology, event_unknown_attachment):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='event type has no such attachment'):
            writer.add_ontology(ontology).add_event(event_unknown_attachment).close()


def test_write_event_obscure_error(ontology, event_obscure_error):
    with EDXMLWriter(output=None) as writer:
        with pytest.raises(EDXMLEventValidationError, match='Expecting element event, got weird'):
            writer.add_ontology(ontology).add_event(event_obscure_error).close()


def test_write_event_repair_obscure_error(ontology, event_obscure_error):
    with EDXMLWriter(output=None) as writer:
        writer.enable_auto_repair_normalize('ea', ['b'])
        with pytest.raises(EDXMLEventValidationError, match='Expecting element event, got weird'):
            writer.add_ontology(ontology).add_event(event_obscure_error).close()
