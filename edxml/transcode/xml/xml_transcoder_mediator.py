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

import re

from lxml import etree
from lxml.etree import XPathSyntaxError
from edxml.logger import log
from edxml.transcode import TranscoderMediator


class XmlTranscoderMediator(TranscoderMediator):
    """
    This class is a mediator between a source of XML elements and a set
    of XmlTranscoder implementations that can transcode the XML elements
    into EDXML events.

    Sources can instantiate the mediator and feed it XML elements, while
    record transcoders can register themselves with the mediator in order to
    transcode the types of XML element that they support.
    """

    def __init__(self, output=None):
        super().__init__(output)
        self._transcoder_positions = {}
        self._last_used_transcoder_xpath = None
        self._last_parent_xpath = None
        self._xpath_matchers = {}
        self._transcoder_tags = {}

    def register(self, xpath_expression, transcoder, tag=None):
        """

        Register a record transcoder for processing XML elements matching
        specified XPath expression. The same record transcoder can be registered
        for multiple XPath expressions. The transcoder argument must be a XmlTranscoder
        class or an extension of it.

        The optional tag argument can be used to pass a list of tag names. Only
        the tags in the input XML data that are included in this list will be
        visited while parsing and matched against the XPath expressions
        associated with registered record transcoders. When the argument is not
        used, the tag names will be guessed from the xpath expressions that
        the record transcoders have been registered with. Namespaced tags can be
        specified using James Clark notation::

            {http://www.w3.org/1999/xhtml}html

        The use of EXSLT regular expressions in XPath expressions is supported and
        can be specified like in this example::

            *[re:test(., "^abc$", "i")]

        Note:
          Any record transcoder that registers itself using None
          as the XPath expression is used as the fallback transcoder. The
          fallback transcoder is used to transcode any record that does not
          match any XPath expression of any registered transcoder.

        Args:
          xpath_expression (Optional[str]): XPath of matching XML records
          transcoder (XmlTranscoder): XmlTranscoder
          tag (Optional[str]): XML tag name
        """
        super().register(xpath_expression, transcoder)

        if tag is not None:
            self._transcoder_tags[xpath_expression] = tag
        else:
            if xpath_expression is None:
                raise ValueError("When registering a fallback transcoder, you must supply the tag parameter.")
            self._transcoder_tags[xpath_expression] = self.get_visited_tag_name(xpath_expression)

        if xpath_expression is None:
            return

        # Create and cache a compiled function for evaluating the
        # XPath expression.
        try:
            self._xpath_matchers[xpath_expression] = etree.XPath(
                xpath_expression, namespaces={
                    're': 'http://exslt.org/regular-expressions'}
            )
        except XPathSyntaxError:
            raise ValueError(
                'Attempt to register record transcoder %s using invalid XPath expression %s.' %
                (type(transcoder).__name__, xpath_expression)
            )

    def _get_transcoder(self, xpath_expression=None):
        """

        Returns a XmlTranscoder instance for transcoding
        XML elements matching specified XPath expression, or None
        if no record transcoder has been registered for the XPath
        expression.

        Args:
          xpath_expression (str): XPath expression matching input element

        Returns:
          edxml.transcode.xml.XmlTranscoder:
        """
        return super()._get_transcoder(xpath_expression)

    def parse(self, input_file, attribute_defaults=False, dtd_validation=False, load_dtd=False, no_network=True,
              remove_blank_text=False, remove_comments=False, remove_pis=False, encoding=None, html=False, recover=None,
              huge_tree=False, schema=None, resolve_entities=False):
        """

        Parses the specified file, writing the resulting EDXML data into the
        output. The file can be any file-like object, or the name of a file
        that should be opened and parsed.

        The other keyword arguments are passed directly to :class:`lxml.etree.iterparse`,
        please refer to the lxml documentation for details.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Notes:
          Passing a file name rather than a file-like object
          is preferred and may result in a small performance gain.

        Args:
          schema: an XMLSchema to validate against
          huge_tree (bool): disable security restrictions and support very deep trees and
                            very long text content (only affects libxml2 2.7+)
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
          input_file (Union[io.TextIOBase, file, str]):

        """
        tags = self._get_tags()

        element_iterator = etree.iterparse(
            input_file, events=['end'], tag=tags, attribute_defaults=attribute_defaults, dtd_validation=dtd_validation,
            load_dtd=load_dtd, no_network=no_network, remove_blank_text=remove_blank_text,
            remove_comments=remove_comments, remove_pis=remove_pis, encoding=encoding, html=html, recover=recover,
            huge_tree=huge_tree, schema=schema, resolve_entities=resolve_entities
        )

        root = None

        for action, elem in element_iterator:
            if root is None:
                root = elem
                while root.getparent() is not None:
                    root = root.getparent()

            tree = etree.ElementTree(root)
            self.process(elem, tree)

    def generate(self, input_file, attribute_defaults=False, dtd_validation=False, load_dtd=False,
                 no_network=True, remove_blank_text=False, remove_comments=False, remove_pis=False, encoding=None,
                 html=False, recover=None, huge_tree=False, schema=None, resolve_entities=False):
        """

        Parses the specified file, yielding bytes containing the resulting
        EDXML data while parsing. The file can be any file-like object,
        or the name of a file that should be opened and parsed.

        If an output was specified when instantiating this class, the EDXML
        data will be written into the output and this generator will yield
        empty strings.

        The other keyword arguments are passed directly to :class:`lxml.etree.iterparse`,
        please refer to the lxml documentation for details.

        Notes:
          Passing a file name rather than a file-like object
          is preferred and may result in a small performance gain.

        Args:
          schema: an XMLSchema to validate against
          huge_tree (bool): disable security restrictions and support very deep trees and
                            very long text content (only affects libxml2 2.7+)
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
          input_file (Union[io.TextIOBase, file, str]):

        """
        tags = self._get_tags()

        element_iterator = etree.iterparse(
            input_file, events=['end'], tag=tags, attribute_defaults=attribute_defaults, dtd_validation=dtd_validation,
            load_dtd=load_dtd, no_network=no_network, remove_blank_text=remove_blank_text,
            remove_comments=remove_comments, remove_pis=remove_pis, encoding=encoding, html=html,
            recover=recover, huge_tree=huge_tree, schema=schema, resolve_entities=resolve_entities
        )

        root = None

        for action, elem in element_iterator:
            if root is None:
                root = elem
                while root.getparent() is not None:
                    root = root.getparent()

            tree = etree.ElementTree(root)
            yield self.process(elem, tree)

        yield self.close()

    def process(self, element, tree=None):
        """
        Processes a single XML element, invoking the correct
        record transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Args:
          element (etree.Element): XML element
          tree (etree.ElementTree): Root of XML document being parsed

        Returns:
          bytes: Generated output XML data
        """

        # Get the XPath expression that matches the element. Note that this
        # is an XPath that matches only this one element, while record transcoders are
        # registered on XPath expressions that are much more generic and typically
        # match multiple elements.
        element_xpath = tree.getpath(element)

        transcoder_xpaths = list(self._xpath_matchers.keys())

        matching_element_xpath = None

        if self._last_used_transcoder_xpath is not None:
            # Try whatever record transcoder was used on the previously
            # transcoded element first. If it matches, we are lucky and we
            # do not need to try them all.
            transcoder_xpaths.insert(0, self._last_used_transcoder_xpath)

        # Below, we try to match the XPath expressions of each of the registered
        # record transcoders with the XPath expression of the current element.
        for matching_xpath in transcoder_xpaths:
            if element in self._xpath_matchers[matching_xpath](tree):
                # The element is among the elements that match the
                # XPath expression of one of the record transcoders.
                matching_element_xpath = matching_xpath
                break

        if matching_element_xpath is not None:
            self._last_used_transcoder_xpath = matching_element_xpath

        transcoder = self._get_transcoder(matching_element_xpath)

        if transcoder:
            if matching_element_xpath is None and self._warn_fallback:
                log.warning(
                    'XML element at %s does not match any XPath expressions, passing to fallback transcoder' %
                    tree.getpath(element)
                )

            self._transcode(element, element_xpath, matching_element_xpath, transcoder)

            # Delete previously transcoded elements to keep the in-memory XML
            # tree small and processing efficient. Note that lxml only allows us
            # to delete children of a parent element by index. Also, we cannot delete
            # the element that we are currently processing, we always delete the
            # previously transcoded element. To this end, we keep track of the
            # indices of the last transcoded element inside its parent element.
            parent = element.getparent()
            parent_xpath = tree.getpath(parent)
            if self._last_parent_xpath is not None:
                last_parent, last_transcoded = self._transcoder_positions.get(self._last_parent_xpath, (None, None))
                if last_transcoded is not None:
                    del last_parent[last_transcoded]

            index = parent.index(element)
            self._transcoder_positions[parent_xpath] = (parent, index)
            self._last_parent_xpath = parent_xpath

            if index > 100:
                log.warning(
                    "The element at xpath %s contains many child elements that have no associated record transcoder. "
                    "These elements are clogging the in-memory XML tree, slowing down processing." % parent_xpath
                )

        else:
            if self._warn_no_transcoder:
                log.warning(
                    'XML element at %s does not match any XPath expressions and no fallback transcoder is available.'
                    % element_xpath
                )
                log.warning('XML element was: %s' % etree.tostring(element, pretty_print=True, encoding='unicode'))

        self._num_input_records_processed += 1

        return self._writer.flush()

    def _get_tags(self):
        """
        Returns the names of the XML tags the XML parser will visit
        while parsing input. By default, these are the tags for which
        record transcoders are registered. This list can be extended
        by overriding this method.

        Returns:
            List[str]

        """
        return list(self._transcoder_tags.values())

    @staticmethod
    def get_visited_tag_name(xpath):
        """
        Tries to determine the name of the tag of elements that match the
        specified XPath expression. Raises ValueError in case the xpath expression
        is too complex to determine the tag name.

        Returns:
             Optional[List[str]]

        """
        if re.search(r"^/?([0-9a-zA-Z_-]+)(/[0-9a-zA-Z_-]+)*$", xpath):
            return xpath.split('/')[-1]

        # The xpath expression is not a simple path,
        # like /some/path/to/tagname.
        raise ValueError(
            'Cannot translate xpath expression %s to a single name of matching tags. '
            'You must explicitly pass a tag name to register the associated record transcoder.' % xpath
        )
