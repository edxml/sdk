from lxml import etree
from edxml.transcode import TranscoderTestHarness


class XmlTranscoderTestHarness(TranscoderTestHarness):

    def __init__(self, fixtures_path, transcoder):
        """
        Creates a new test harness for testing specified transcoder
        using XML fixtures stored at the indicated path.

        Args:
            fixtures_path (str): Path to the fixtures set
            transcoder (edxml.transcode.Transcoder): The transcoder under test
        """
        super(XmlTranscoderTestHarness, self).__init__(transcoder)
        self.fixtures_path = fixtures_path

    def process_xml(self, filename, transcoder_root='/', element_root=None):
        """
        Parses specified XML file and transcodes it to produce output
        events. The output events are added to the event set. The filename
        argument must be a path relative to the fixtures path.

        The XML file is expected to be structured like real input data
        stripped down to contain the XML elements that are relevant to
        the transcoder under test.

        The transcoder_root is the XPath expression that the transcoder
        would be registered at. It will be used to extract the input
        elements for the transcoder from the parsed XML file, exactly
        as XmlTranscoderMediator would do it on real data.

        The element_root is the XPath expression that is used to find
        the root of the element inside the parsed XML file. When unspecified,
        it will be fetched from the TYPE_MAP constant of the transcoder.

        Args:
            filename (str): The XML file to use as input record fixture
            element_root:
            transcoder_root:
        """
        if element_root is None:
            if len(self.transcoder.TYPE_MAP.keys()) > 1:
                raise Exception(
                    'No element root was specified for transcoding XML element using %s. '
                    'You must specify one because this transcoder has multiple element roots in its TYPE_MAP.'
                    % type(self.transcoder).__name__
                )
            element_root = list(self.transcoder.TYPE_MAP.keys())[0]

        element = etree.fromstring(open(self.fixtures_path.rstrip('/') + '/' + filename, 'rb').read())
        for sub_element in element.xpath(transcoder_root):
            self.process(sub_element, selector=element_root)
        self.close()
