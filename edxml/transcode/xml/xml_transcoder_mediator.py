# -*- coding: utf-8 -*-

from lxml import etree
from lxml.etree import XPathSyntaxError
from edxml.EDXMLBase import EDXMLError
from edxml.transcode import TranscoderMediator


class XmlTranscoderMediator(TranscoderMediator):
  """
  This class is a mediator between a source of XML elements and a set
  of XmlTranscoder implementations that can transcode the XML elements
  into EDXML events.

  Sources can instantiate the mediator and feed it XML elements, while
  transcoders can register themselves with the mediator in order to
  transcode the types of XML element that they support.
  """

  _XPATH_MATCHERS = {}

  @classmethod
  def Register(cls, XPathExpression, Transcoder):
    """

    Register a transcoder for processing XML elements matching
    specified XPath expression. The same transcoder can be registered
    for multiple XPath expressions. The Transcoder argument must be a XmlTranscoder
    class or an extension of it. Do not pass in instantiated
    class, pass the class itself.

    The use of EXSLT regular expressions in XPath expressions is supported and
    can be specified like in this example::

        *[re:test(., "^abc$", "i")]

    Note:
      Any transcoder that registers itself as a transcoder for the
      XPath expression 'RECORD_OF_UNKNOWN_TYPE' is used as the fallback
      transcoder. The fallback transcoder is used to transcode any record
      that does not match any XPath expression of any registered transcoder.

    Args:
      XPathExpression (str): XPath of matching XML records
      Transcoder (XmlTranscoder): XmlTranscoder class
    """
    TranscoderMediator.Register(XPathExpression, Transcoder)

    # Create and cache a compiled function for evaluating the
    # XPath expression.
    try:
      cls._XPATH_MATCHERS[XPathExpression] = etree.XPath(
        XPathExpression, namespaces={'re': 'http://exslt.org/regular-expressions'}
      )
    except XPathSyntaxError:
      raise ValueError('Attempt to register transcoder %s using invalid XPath expression %s.' % (Transcoder.__class__, XPathExpression))

  @classmethod
  def GetTranscoder(cls, XPathExpression):
    """

    Returns a XmlTranscoder instance for transcoding
    XML elements matching specified XPath expression, or None
    if no transcoder has been registered for the XPath
    expression.

    Args:
      XPathExpression (str): XPath expression matching input element

    Returns:
      edxml.transcode.xml.XmlTranscoder:
    """
    return TranscoderMediator.GetTranscoder(XPathExpression)

  def Parse(self, inputFile, tags, attribute_defaults=False, dtd_validation=False, load_dtd=False, no_network=True,
            remove_blank_text=False, remove_comments=False, remove_pis=False, encoding=None, html=False, recover=None,
            huge_tree=False, schema=None, resolve_entities=False):
    """

    Parses the specified file. The file can be any
    file-like object, or the name of a file that should
    be opened and parsed.

    The tags argument is a list of tag names. Only the tags in the input
    XML data that are included in this list will be matched against the
    XPath expressions associated with registered transcoders. So, all
    tags of XML elements that should be provided to transcoders must be
    included in this list. Other XML elements cannot be transcoded into
    EDXML events, even though they can still be addressed by traversing
    the XML tree. However, do note that the mediator uses etree.iterparse
    to parse the input XML data, so the XML tree will be incomplete while
    parsing. Namespaced tags can be specified by inclusing the namespace
    like this:

      {http://www.w3.org/1999/xhtml}html

    The other keyword arguments are passed directly to :class:`lxml.etree.iterparse`,
    please refer to the lxml documentation for details.

    Notes:
      Passing a file name rather than a file-like object
      is preferred and may result in a small performance gain.

    Args:
      schema: an XMLSchema to validate against
      huge_tree (bool): disable security restrictions and support very deep trees and very long text content (only affects libxml2 2.7+)
      recover (bool): try hard to parse through broken input (default: True for HTML, False otherwise)
      html (bool): parse input as HTML (default: XML)
      encoding: override the document encoding
      remove_pis (bool): discard processing instructions
      remove_comments (bool): discard comments
      remove_blank_text (bool): discard blank text nodes
      no_network (bool): prevent network access for related files
      load_dtd (bool): use DTD for parsing
      dtd_validation (bool): validate (if DTD is available)
      attribute_defaults (bool): read default attributes from DTD
      resolve_entities (bool): replace entities by their text value (default: True)
      tags (List[str]): List of filtered tag names
      inputFile (Union[io.TextIOBase, file, str]):

    """
    elementIterator = etree.iterparse(
      inputFile, events=['end'], tag=tags, attribute_defaults=attribute_defaults, dtd_validation=dtd_validation, load_dtd=load_dtd,
      no_network=no_network, remove_blank_text=remove_blank_text, remove_comments=remove_comments, remove_pis=remove_pis, encoding=encoding, html=html,
      recover=recover, huge_tree=huge_tree, schema=schema, resolve_entities=resolve_entities
    )

    root = None

    for action, elem in elementIterator:
      if root is None:
        root = elem
        while root.getparent() is not None:
          root = root.getparent()

      Tree = etree.ElementTree(root)
      self.Process(elem, Tree)

      # Delete previously parsed elements
      while elem.getprevious() is not None:
        del elem.getparent()[0]

    if self._writer:
      self._writer.Close()

  def Process(self, Element, Tree=None):
    """
    Processes a single XML element, invoking the correct
    transcoder to generate an EDXML event and writing the
    event into the output.

    Args:
      Element (etree.Element): XML element
    """

    # Get the XPath expression that matches the element. Note that this
    # is an XPath that matches only this one element, while transcoders are
    # registered on XPath expressions that are much more generic and typically
    # match multiple elements.
    ElementXPath = Tree.getpath(Element)

    # Matching elements to the correct transcoders for processing them requires
    # that we try to match the element to each of the XPath expressions that are
    # associated with the transcoders. However, we do expect the left hand side of
    # the element XPath to match the left hand side of the transcoder XPath. So,
    # we sort the transcoder XPath expressions such that these left hand matching
    # ones are tested first.
    TranscoderPaths = sorted(XmlTranscoderMediator._XPATH_MATCHERS.keys(), key=lambda xpath: ElementXPath.startswith(xpath))

    MatchingElementXPath = 'RECORD_OF_UNKNOWN_TYPE'

    for MatchingXPath in TranscoderPaths:
      if Element in XmlTranscoderMediator._XPATH_MATCHERS[MatchingXPath](Element):
        # The element is among the elements that match the
        # XPath expression of one of the transcoders.
        MatchingElementXPath = MatchingXPath
        break

    Transcoder = self.GetTranscoder(MatchingElementXPath)

    if Transcoder:
      if ElementXPath == 'RECORD_OF_UNKNOWN_TYPE' and self._warn_fallback:
        self.Warning(
          'XML element at %s does not match any XPath expressions, passing to fallback transcoder' %
          Tree.getpath(Element)
        )

      for Event in Transcoder.Generate(Element, MatchingElementXPath):
        if not self._writer:
          # Apparently, this is the first event that
          # is generated. Create an EDXML writer and
          # write the initial ontology.
          self._create_writer()
          self._write_initial_ontology()
        if self._ontology.IsModifiedSince(self._last_written_ontology_version):
          # Ontology was changed since we wrote the last ontology update,
          # so we need to write another update.
          self._write_ontology_update()
          self._last_written_ontology_version = self._ontology.GetVersion()

        if self._transcoderIsPostprocessor(Transcoder):
          try:
            for PostProcessedEvent in Transcoder.PostProcess(Event):
              try:
                self._writer.AddEvent(PostProcessedEvent)
              except EDXMLError as Except:
                if not self._ignore_invalid_events:
                  raise
                if self._warn_invalid_events:
                  self.Warning(('The post processor of the transcoder for XML element at %s produced '
                                'an invalid event: %s\n\nContinuing...') % (ElementXPath, str(Except))
                               )
          except Exception as Except:
            if self._debug:
              raise
            self.Warning(('The post processor of the transcoder for XML element at %s failed '
                          'with %s: %s\n\nContinuing...') % (ElementXPath, type(Except).__name__, str(Except))
                         )
        else:
          try:
            self._writer.AddEvent(Event)
          except EDXMLError as Except:
            if not self._ignore_invalid_events:
              raise
            if self._warn_invalid_events:
              self.Warning(('The transcoder for XML element at %s produced an invalid '
                            'event: %s\n\nContinuing...') % (ElementXPath, str(Except)))
          except Exception as Except:
            if not self._ignore_invalid_events or self._debug:
              raise
            if self._warn_invalid_events:
              self.Warning(('Transcoder for XML element at %s failed '
                            'with %s: %s\n\nContinuing...') % (ElementXPath, type(Except).__name__, str(Except))
                           )
    else:
      if self._warn_no_transcoder:
        self.Warning(
          'XML element at %s does not match any XPath expressions and no fallback transcoder is available.'
          % ElementXPath
        )
        self.Warning('XML element was: %s' % etree.tostring(Element, pretty_print=True))
