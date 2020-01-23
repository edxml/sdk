from io import BytesIO

import pytest
from lxml import etree, objectify

from edxml.error import EDXMLValidationError
from edxml.transcode.xml import XmlTranscoderMediator, XmlTranscoder


@pytest.fixture()
def xml():
    return bytes(
        '<root>'
        '  <records>'
        '    <a>'
        '      <p1>a1</p1>'
        '    </a>'
        '    <b attr="b1"/>'
        '    <a>'
        '      <p1>a2</p1>'
        '    </a>'
        '    <b attr="b2"/>'
        '  </records>'
        '</root>', encoding='utf-8'
    )


@pytest.fixture()
def output():
    class Output(BytesIO):
        # For transcoding we need a file-like output
        # object that is in append mode.
        mode = 'ba'

    return Output()


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


def test_complex_mediator_xpath_exception(xml_transcoder):
    mediator = XmlTranscoderMediator()
    with pytest.raises(ValueError, match='You must explicitly pass a tag name to register'):
        mediator.register('//some/complicated[0]/xpath', xml_transcoder)


def test_invalid_mediator_xpath_exception(xml_transcoder):
    mediator = XmlTranscoderMediator()
    with pytest.raises(ValueError, match='invalid XPath'):
        mediator.register(']', xml_transcoder, tag='test')


def test_duplicate_registration_exception(xml_transcoder):
    mediator = XmlTranscoderMediator()
    with pytest.raises(Exception, match='Attempt to register multiple transcoders'):
        mediator.register('/some/path', xml_transcoder, tag='test')
        mediator.register('/some/path', xml_transcoder, tag='test')


def test_parse_single_transcoder_single_event_type(xml_transcoder, xml, output):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    with XmlTranscoderMediator(output) as mediator:
        mediator.register('records', xml_transcoder)
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/event')) == 2
    assert len(edxml_extract(edxml, '/edxml/event/properties/*')) == 2
    assert edxml_extract(edxml, '/edxml/event[1]/properties/property-a')[0].text == 'a1'
    assert edxml_extract(edxml, '/edxml/event[2]/properties/property-a')[0].text == 'a2'
    assert edxml_extract(edxml, '/edxml/event')[0].attrib == {
        'event-type': 'test-event-type.a',
        'source-uri': '/test/uri/'
    }

    XmlTranscoderMediator.clear_registrations()


def test_generate(xml_transcoder, xml):
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    with XmlTranscoderMediator() as mediator:
        mediator.register('records', xml_transcoder)
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        output_strings = list(mediator.generate(BytesIO(xml)))

    edxml = etree.fromstring(b''.join(output_strings))

    assert len(edxml_extract(edxml, '/edxml/event')) == 2

    XmlTranscoderMediator.clear_registrations()


def test_parse_nested_transcoders(xml, output):

    class InnerTranscoder(XmlTranscoder):
        def create_object_types(self):
            self._ontology.create_object_type('object-type.string')

    class OuterTranscoder(InnerTranscoder):
        pass

    # We will prepare two transcoders, one will process the /root/records
    # element while another will process the /root/records/a inside it.
    # We test this scenario because the mediator will remove transcoded
    # elements from the in memory XML tree while parsing it. Removing the
    # transcoded elements that are interleaved with other elements that must
    # remain untouched is tricky.

    # Below we create a transcoder that we will register on /root/records/a. It
    # will transcode the elements that it is registered at (self, or '.')
    InnerTranscoder.TYPE_MAP = {'.': 'test-event-type.a'}
    InnerTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    InnerTranscoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    # Below we create a transcoder that we will register on /root/records. It
    # will be invoked at the records end tag, after the /root/records/a records
    # will have been transcoded using inner_transcoder. When cleaning of the
    # in memory XML tree is done properly, the outer transcoder will still have
    # the /root/records/b elements to transcode while the /root/records/a elements
    # are gone. Except for the last one, because the mediator cannot remove the
    # element that it is currently processing. It removes the previous one.
    OuterTranscoder.TYPE_MAP = {
        'a': 'test-event-type.a',
        'b': 'test-event-type.b'
    }
    OuterTranscoder.TYPE_PROPERTIES = {
        'test-event-type.a': {'property-a': 'object-type.string'},
        'test-event-type.b': {'property-b': 'object-type.string'}
    }
    OuterTranscoder.PROPERTY_MAP = {
        'test-event-type.a': {'p1': 'property-a'},
        'test-event-type.b': {'@attr': 'property-b'}
    }

    XmlTranscoderMediator.register('/root/records', OuterTranscoder)
    XmlTranscoderMediator.register('/root/records/a', InnerTranscoder)

    with XmlTranscoderMediator(output) as mediator:
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/event')) == 4 + 1
    assert len(edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]')) == 2 + 1
    assert len(edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.b"]')) == 2
    assert len(edxml_extract(edxml, '/edxml/event/properties/*')) == 4 + 1
    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[0].text == 'a1'
    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[1].text == 'a2'
    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[2].text == 'a2'
    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.b"]/properties/property-b')[0].text == 'b1'
    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.b"]/properties/property-b')[1].text == 'b2'

    XmlTranscoderMediator.clear_registrations()


def test_log_skipped_element(xml_transcoder, xml, output, caplog):

    # Below we deliberately set the tag that the parser should visit
    # to 'b' while we register a transcoder for elements having tag 'a'
    XmlTranscoderMediator.register('/root/records/a', xml_transcoder, tag='b')

    with XmlTranscoderMediator(output) as mediator:
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    assert '/root/records/b[1] does not match any XPath' in ''.join(caplog.messages)
    assert '/root/records/b[2] does not match any XPath' in ''.join(caplog.messages)

    XmlTranscoderMediator.clear_registrations()


def test_log_fallback_transcoder(xml_transcoder, xml, output, caplog):

    XmlTranscoderMediator.register(None, xml_transcoder, tag='records')

    with XmlTranscoderMediator(output) as mediator:
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    assert 'passing to fallback transcoder' in ''.join(caplog.messages)

    XmlTranscoderMediator.clear_registrations()


def test_ontology_update(xml_transcoder, xml, output):

    class SourceGeneratingMediator(XmlTranscoderMediator):
        def process(self, element, tree=None):
            super(SourceGeneratingMediator, self).process(element, tree)
            # After processing each element and outputting the resulting
            # event we generate an EDXML source uri that was not initially
            # added to the mediator. This forces the mediator to output
            # an ontology update after the first event was written,
            # resulting in two ontology elements in the EDXML output.
            self.add_event_source('/another/test/uri/')

    xml_transcoder.TYPE_MAP = {'.': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    SourceGeneratingMediator.register('/root/records/a', xml_transcoder)

    with SourceGeneratingMediator(output) as mediator:
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/ontology')) == 2
    assert len(edxml_extract(edxml, '/edxml/ontology/sources/source[@uri="/another/test/uri/"]')) == 1

    XmlTranscoderMediator.clear_registrations()


def test_invalid_event_exception(xml_transcoder, xml, output):

    # Note that we use 'object-type.integer' as object type
    # while the values in the XML are not integer.
    xml_transcoder.TYPE_MAP = {'.': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.integer'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    XmlTranscoderMediator.register('/root/records/a', xml_transcoder)

    with pytest.raises(EDXMLValidationError, match='invalid event'):
        with XmlTranscoderMediator(output) as mediator:
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.parse(BytesIO(xml))

    XmlTranscoderMediator.clear_registrations()


def test_post_process(xml_transcoder, xml, output):

    class PostProcessingTranscoder(xml_transcoder):
        def post_process(self, event, input_record):
            # Change the property value by fetching an attribute from a sibling
            # element. This changes the property values of the output events
            # from 'a1' / 'a2' to 'b1'.
            event['property-a'] = input_record.find('../b').attrib['attr']
            yield event

    PostProcessingTranscoder.TYPE_MAP = {'.': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    XmlTranscoderMediator.register('/root/records/a', PostProcessingTranscoder)

    with XmlTranscoderMediator(output) as mediator:
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[0].text == 'b1'

    XmlTranscoderMediator.clear_registrations()


def test_post_processor_invalid_event_exception(xml_transcoder, xml, output):

    class PostProcessingTranscoder(xml_transcoder):
        def post_process(self, event, element):
            # Change the event to be invalid
            event['nonexistent-property'] = 'test'
            yield event

    PostProcessingTranscoder.TYPE_MAP = {'.': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    XmlTranscoderMediator.register('/root/records/a', PostProcessingTranscoder)

    with pytest.raises(EDXMLValidationError, match='invalid event'):
        with XmlTranscoderMediator(output) as mediator:
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.parse(BytesIO(xml))

    XmlTranscoderMediator.clear_registrations()
