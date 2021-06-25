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

import pytest
from lxml import etree

from conftest import edxml_extract
from edxml.error import EDXMLEventValidationError
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
    with pytest.raises(Exception, match='Attempt to register multiple record transcoders'):
        mediator.register('/some/path', xml_transcoder, tag='test')
        mediator.register('/some/path', xml_transcoder, tag='test')


def test_parse_single_transcoder_single_event_type(xml_transcoder, xml):
    xml_transcoder.TYPES = ['test-event-type.a']
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    output = BytesIO()

    with XmlTranscoderMediator(output) as mediator:
        mediator.register('records', xml_transcoder())
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


def test_generate(xml_transcoder, xml):
    xml_transcoder.TYPES = ['test-event-type.a']
    xml_transcoder.TYPE_MAP = {'a': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    with XmlTranscoderMediator() as mediator:
        mediator.register('records', xml_transcoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        output_strings = list(mediator.generate(BytesIO(xml)))

    edxml = etree.fromstring(b''.join(output_strings))

    assert len(edxml_extract(edxml, '/edxml/event')) == 2


def test_parse_nested_transcoders(xml):

    class InnerTranscoder(XmlTranscoder):
        def create_object_types(self):
            self._ontology.create_object_type('object-type.string')

    class OuterTranscoder(InnerTranscoder):
        pass

    # We will prepare two record transcoders, one will process the /root/records
    # element while another will process the /root/records/a inside it.
    # We test this scenario because the mediator will remove transcoded
    # elements from the in memory XML tree while parsing it. Removing the
    # transcoded elements that are interleaved with other elements that must
    # remain untouched is tricky.

    # Below we create a record transcoder that we will register on /root/records/a. It
    # will transcode the elements that it is registered at (self, or '.')
    InnerTranscoder.TYPES = ['inner.a']
    InnerTranscoder.TYPE_MAP = {'.': 'inner.a'}
    InnerTranscoder.TYPE_PROPERTIES = {'inner.a': {'property-a': 'object-type.string'}}
    InnerTranscoder.PROPERTY_MAP = {'inner.a': {'p1': 'property-a'}}

    # Below we create a record transcoder that we will register on /root/records. It
    # will be invoked at the records end tag, after the /root/records/a records
    # will have been transcoded using inner_transcoder. When cleaning of the
    # in memory XML tree is done properly, the outer transcoder will still have
    # the /root/records/b elements to transcode while the /root/records/a elements
    # are gone. Except for the last one, because the mediator cannot remove the
    # element that it is currently processing. It removes the previous one.
    OuterTranscoder.TYPES = ['outer.a', 'outer.b']
    OuterTranscoder.TYPE_MAP = {
        'a': 'outer.a',
        'b': 'outer.b'
    }
    OuterTranscoder.TYPE_PROPERTIES = {
        'outer.a': {'property-a': 'object-type.string'},
        'outer.b': {'property-b': 'object-type.string'}
    }
    OuterTranscoder.PROPERTY_MAP = {
        'outer.a': {'p1': 'property-a'},
        'outer.b': {'@attr': 'property-b'}
    }

    output = BytesIO()

    with XmlTranscoderMediator(output) as mediator:
        mediator.register('/root/records', OuterTranscoder())
        mediator.register('/root/records/a', InnerTranscoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/event')) == 4 + 1
    assert len(edxml_extract(edxml, '/edxml/event[@event-type="inner.a"]')) == 2
    assert len(edxml_extract(edxml, '/edxml/event[@event-type="outer.a"]')) == 1
    assert len(edxml_extract(edxml, '/edxml/event[@event-type="outer.b"]')) == 2
    assert len(edxml_extract(edxml, '/edxml/event/properties/*')) == 4 + 1
    assert edxml_extract(edxml, '/edxml/event[@event-type="inner.a"]/properties/property-a')[0].text == 'a1'
    assert edxml_extract(edxml, '/edxml/event[@event-type="inner.a"]/properties/property-a')[1].text == 'a2'
    assert edxml_extract(edxml, '/edxml/event[@event-type="outer.a"]/properties/property-a')[0].text == 'a2'
    assert edxml_extract(edxml, '/edxml/event[@event-type="outer.b"]/properties/property-b')[0].text == 'b1'
    assert edxml_extract(edxml, '/edxml/event[@event-type="outer.b"]/properties/property-b')[1].text == 'b2'


def test_log_skipped_element(xml_transcoder, xml, caplog):

    with XmlTranscoderMediator(BytesIO()) as mediator:
        # Below we deliberately set the tag that the parser should visit
        # to 'b' while we register a record transcoder for elements having tag 'a'
        mediator.register('/root/records/a', xml_transcoder(), tag='b')

        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    assert '/root/records/b[1] does not match any XPath' in ''.join(caplog.messages)
    assert '/root/records/b[2] does not match any XPath' in ''.join(caplog.messages)


def test_log_fallback_transcoder(xml_transcoder, xml, caplog):

    with XmlTranscoderMediator(BytesIO()) as mediator:
        mediator.register(None, xml_transcoder(), tag='records')
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    assert 'passing to fallback transcoder' in ''.join(caplog.messages)


def test_ontology_update(xml_transcoder, xml):

    class SourceGeneratingMediator(XmlTranscoderMediator):
        def __init__(self, output):
            super().__init__(output)
            self.source_added = False

        def process(self, element, tree=None):
            super().process(element, tree)
            # After processing each element and outputting the resulting
            # event we generate an EDXML source uri that was not initially
            # added to the mediator. This forces the mediator to output
            # an ontology update after the first event was written,
            # resulting in two ontology elements in the EDXML output.
            if not self.source_added:
                self.add_event_source('/another/test/uri/')
                self.source_added = True

    xml_transcoder.TYPES = ['test-event-type.a']
    xml_transcoder.TYPE_MAP = {'.': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    output = BytesIO()

    with SourceGeneratingMediator(output) as mediator:
        mediator.register('/root/records/a', xml_transcoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert len(edxml_extract(edxml, '/edxml/ontology')) == 2
    assert len(edxml_extract(edxml, '/edxml/ontology/sources/source[@uri="/another/test/uri/"]')) == 1


def test_invalid_event_exception(xml_transcoder, xml):

    # Note that we use 'object-type.integer' as object type
    # while the values in the XML are not integer.
    xml_transcoder.TYPES = ['test-event-type.a']
    xml_transcoder.TYPE_MAP = {'.': 'test-event-type.a'}
    xml_transcoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.integer'}}
    xml_transcoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    with pytest.raises(EDXMLEventValidationError, match='invalid event'):
        with XmlTranscoderMediator(BytesIO()) as mediator:
            mediator.register('/root/records/a', xml_transcoder())
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.parse(BytesIO(xml))


def test_post_process(xml_transcoder, xml):

    class PostProcessingTranscoder(xml_transcoder):
        def post_process(self, event, input_record):
            # Change the property value by fetching an attribute from a sibling
            # element. This changes the property values of the output events
            # from 'a1' / 'a2' to 'b1'.
            event['property-a'] = input_record.find('../b').attrib['attr']
            yield event

    PostProcessingTranscoder.TYPES = ['test-event-type.a']
    PostProcessingTranscoder.TYPE_MAP = {'.': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    output = BytesIO()

    with XmlTranscoderMediator(output) as mediator:
        mediator.register('/root/records/a', PostProcessingTranscoder())
        mediator.add_event_source('/test/uri/')
        mediator.set_event_source('/test/uri/')
        mediator.debug()
        mediator.parse(BytesIO(xml))

    edxml = etree.fromstring(output.getvalue())

    assert edxml_extract(edxml, '/edxml/event[@event-type="test-event-type.a"]/properties/property-a')[0].text == 'b1'


def test_post_processor_invalid_event_exception(xml_transcoder, xml):

    class PostProcessingTranscoder(xml_transcoder):
        def post_process(self, event, element):
            # Change the event to be invalid
            event['nonexistent-property'] = 'test'
            yield event

    PostProcessingTranscoder.TYPES = ['test-event-type.a']
    PostProcessingTranscoder.TYPE_MAP = {'.': 'test-event-type.a'}
    PostProcessingTranscoder.TYPE_PROPERTIES = {'test-event-type.a': {'property-a': 'object-type.string'}}
    PostProcessingTranscoder.PROPERTY_MAP = {'test-event-type.a': {'p1': 'property-a'}}

    with pytest.raises(EDXMLEventValidationError, match='invalid event'):
        with XmlTranscoderMediator(BytesIO()) as mediator:
            mediator.register('/root/records/a', PostProcessingTranscoder())
            mediator.add_event_source('/test/uri/')
            mediator.set_event_source('/test/uri/')
            mediator.debug()
            mediator.parse(BytesIO(xml))
