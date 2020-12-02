from io import BytesIO

import pytest
from lxml import etree, objectify

from edxml.error import EDXMLValidationError
from edxml.ontology import DataType
from edxml.transcode.object import ObjectTranscoderMediator, ObjectTranscoder


@pytest.fixture()
def record():
    return {
        'type': 'test_record',
        'records': {
            'a': ['a1', 'a2'],
            'b': ['b1', 'b2']
        }
    }


@pytest.fixture()
def object_transcoder():
    class TestObjectTranscoder(ObjectTranscoder):
        """
        This extension of ObjectTranscoder allows us to set class attributes
        on it that last for just one unit test, making sure that unit
        tests are free of side effects. Setting class attributes on the
        ObjectTranscoder class would cause side effects because that class is
        shared by all tests.
        """
        def create_object_types(self):
            self._ontology.create_object_type('object-type.string')
            self._ontology.create_object_type('object-type.integer', data_type=DataType.int().get())

        @classmethod
        def create_event_type(cls, event_type_name, ontology):
            event_type = super().create_event_type(event_type_name, ontology)

            for prop in event_type.get_properties().values():
                # For convenience we make all properties multi-valued to
                # allow running tests that yield multi-valued properties.
                prop.make_multivalued()

            return event_type

    return TestObjectTranscoder


def edxml_extract(edxml, path):
    # Below, we remove the EDXML namespace from all
    # tags, allowing us to use simple XPath expressions
    # without namespaces. We can safely do this because
    # our tests do not generate foreign elements.
    for elem in edxml.getiterator():
        if not hasattr(elem.tag, 'find'):
            continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    objectify.deannotate(edxml, cleanup_namespaces=True)

    return edxml.xpath(path)


def test_duplicate_registration_exception(object_transcoder):
    with pytest.raises(Exception, match='Attempt to register multiple record transcoders'):
        mediator = ObjectTranscoderMediator()
        mediator.register('test_record', object_transcoder())
        mediator.register('test_record', object_transcoder())


def test_process_single_transcoder_single_event_type(object_transcoder_mediator, object_transcoder, record):
    object_transcoder.TYPE_MAP = {'test_record': 'test-event-type.a'}
    object_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    object_transcoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    output = BytesIO()

    with object_transcoder_mediator(output) as mediator:
        mediator.register('test_record', object_transcoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.process(record)

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/event')) == 1
    assert len(edxml_extract(edxml, '/edxml/event/properties/*')) == 2
    assert set(edxml_extract(edxml, '/edxml/event/properties/property-a/text()')) == {'a1', 'a2'}
    assert edxml_extract(edxml, '/edxml/event')[0].attrib == {
        'event-type': 'test-event-type.a',
        'source-uri': '/test/uri/'
    }


def test_log_fallback_transcoder(object_transcoder_mediator, object_transcoder, record, caplog):

    object_transcoder.TYPE_MAP = {None: 'test-event-type.a'}
    object_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    object_transcoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    # Below, we set the record type to some type for
    # which no record transcoder has been registered.
    record['type'] = 'nonexistent'

    with object_transcoder_mediator(BytesIO()) as mediator:
        mediator.register(None, object_transcoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.process(record)

    assert 'passing to fallback transcoder' in ''.join(caplog.messages)


def test_ontology_update(object_transcoder_mediator, object_transcoder, record):

    class SourceGeneratingMediator(object_transcoder_mediator):

        def __init__(self, output):
            super().__init__(output)
            self.source_added = False

        def process(self, record):
            super().process(record)
            # After processing each element and outputting the resulting
            # event we generate an EDXML source uri that was not initially
            # added to the mediator. This forces the mediator to output
            # an ontology update after the first event was written,
            # resulting in two ontology elements in the EDXML output.
            if not self.source_added:
                self.add_event_source('/another/test/uri/')
                self.source_added = True

    object_transcoder.TYPE_MAP = {'test_record': 'test-event-type.a'}
    object_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    object_transcoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    output = BytesIO()

    with SourceGeneratingMediator(output) as mediator:
        mediator.register('test_record', object_transcoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.process(record)
        mediator.process(record)

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/ontology')) == 2
    assert len(edxml_extract(edxml, '/edxml/ontology/sources/source[@uri="/another/test/uri/"]')) == 1


def test_invalid_event_exception(object_transcoder_mediator, object_transcoder, record):

    # Note that we use 'object-type.integer' as object type
    # while the values in the record are not integer.
    object_transcoder.TYPE_MAP = {'test_record': 'test-event-type.a'}
    object_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.integer'}}
    object_transcoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    with pytest.raises(EDXMLValidationError, match='invalid event'):
        with object_transcoder_mediator(BytesIO()) as mediator:
            mediator.register('test_record', object_transcoder())
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.process(record)


def test_post_process(object_transcoder_mediator, object_transcoder, record):

    class PostProcessingTranscoder(object_transcoder):
        def post_process(self, event, input_record):
            # Change the property value by fetching an attribute from a sibling
            # element. This changes the property values of the output events
            # from 'a1' / 'a2' to 'b1'.
            event['property-a'] = input_record['records']['b'][0]
            yield event

    PostProcessingTranscoder.TYPE_MAP = {'test_record': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    output = BytesIO()

    with object_transcoder_mediator(output) as mediator:
        mediator.register('test_record', PostProcessingTranscoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.process(record)

    edxml = etree.fromstring(output.getvalue())

    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[0].text == 'b1'


def test_post_processor_invalid_event_exception(object_transcoder_mediator, object_transcoder, record):

    class PostProcessingTranscoder(object_transcoder):
        def post_process(self, event, element):
            # Change the event to be invalid
            event['nonexistent-property'] = 'test'
            yield event

    PostProcessingTranscoder.TYPE_MAP = {'test_record': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'records.a': 'property-a'}}

    with pytest.raises(EDXMLValidationError, match='invalid event'):
        with object_transcoder_mediator(BytesIO()) as mediator:
            mediator.register('test_record', PostProcessingTranscoder())
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.process(record)
