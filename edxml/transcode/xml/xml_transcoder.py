# -*- coding: utf-8 -*-

import re
import unicodedata
import edxml.transcode

from edxml import EventElement
from lxml import etree
from lxml.etree import XPathSyntaxError


class XmlTranscoder(edxml.transcode.Transcoder):

    TYPE_MAP = {}
    """
  The TYPE_MAP attribute is a dictionary mapping EDXML event type names
  to the XPath expressions of the equivalent input XML elements. This mapping
  is used by the transcoder mediator to find the correct transcoder for each input
  data record.

  Note:
    When no EDXML event type name is specified for a particular XPath expression,
    it is up to the transcoder to set the event type on the events that it generates.

  Note:
    The fallback transcoder must set the None key to the name of the EDXML
    fallback event type.
  """

    XPATH_MAP = {}
    """
  The XPATH_MAP attribute is a dictionary mapping XPath expressions to EDXML
  event properties. The map is used to automatically populate the properties of
  the EDXMLEvent instances produced by the Generate method of the XmlTranscoder
  class. The keys are XPath expressions relative to the root of the XML input
  elements for this transcoder. Example::

      {'./some/subtag[@attribute]': 'property-name'}

  The use of EXSLT regular expressions is supported and may be used in Xpath keys
  like this::

      {'*[re:test(., "^abc$", "i")]': 'property-name'}

  Extending XPath by injecting custom Python functions is supported due to the lxml
  implementation of XPath that is being used in the transcoder implementation. Please
  refer to the lxml documentation about this subject. This transcoder implementation
  provides a small set of custom XPath functions already, which shows how it is done.

  Note that the event structure will not be validated until the event is yielded by
  the Generate() method. This creates the possibility to add nonexistent properties
  to the XPath map and remove them in the Generate method, which may be convenient
  for composing properties from multiple XML input tags or attributes, or for
  splitting the auto-generated event into multiple output events.
  """

    EMPTY_VALUES = {}
    """
  The EMPTY_VALUES attribute is a dictionary mapping XPath expressions to
  values of the associated property that should be considered empty. As an example,
  the data source might use a specific string to indicate a value that is absent
  or irrelevant, like '-', 'n/a' or 'none'. By listing these values with the XPath
  expression associated with an output event property, the property will be
  automatically omitted from the generated EDXML events. Example::

      {'./some/subtag[@attribute]': ('none', '-')}

  Note that empty values are *always* omitted, because empty values are not permitted
  in EDXML event objects.

  """

    _XPATH_MATCHERS = {}   # type: Dict[str, etree.XPath]

    def __init__(self):
        super(XmlTranscoder, self).__init__()

        # TODO: It would be nicer to put functions into a
        # namespace, but lxml throws weird exceptions on repeated
        # invocations of namespaced functions...
        ns = etree.FunctionNamespace(None)
        ns['findall'] = XmlTranscoder._FindAll
        ns['ctrl_strip'] = XmlTranscoder._StripControlChars
        ns['ws_normalize'] = XmlTranscoder._NormalizeString

    @staticmethod
    def _FindAll(Context, Nodes, Pattern, Flags):
        """

        This function is available as an XPath function named 'findall', in
        the global namespace. It runs re.findall() on the text of a set of XML
        elements, matching the element text to a given regular expression. The
        matches are returned as a list of strings. If the expression contains
        a group, only the substring inside the group is returned.

        The findall function expects a node set as its first argument, which can
        be generated using another XPath expression. The text of all of these nodes
        will be matched. The second argument is the expression. The third argument
        is an ORed combination of the various flags defined in the re module. Example::

          'findall(./some/subtag, "[a-f0-9]*", %d)' % re.IGNORECASE

        Notes:
          The regular expression must not contain more than one group.

        Args:
            Context: lxml function context
            Nodes (List[etree._Element]):
            Pattern Union[str, re.SRE_Pattern]:
            Flags (int): Regular expression flags

        Returns:
          List[unicode]

        """
        TotalMatches = []
        for Node in Nodes:
            if Node.text:
                Matches = re.findall(Pattern, Node.text, int(Flags))
                TotalMatches.extend(unicode(Match) for Match in Matches)
        return TotalMatches

    @staticmethod
    def _StripControlChars(Context, Strings):
        """

        This function is available as an XPath function named 'ctrl_strip', in
        the global namespace. It expects either a single string or a list of
        strings as input. It returns the input, stripping any control characters.
        Example::

          'ctrl_strip(string(./some/subtag))'

        Args:
            Context: lxml function context
            Strings (Union[unicode, List[unicode]): Input strings

        Returns:
          (Union[unicode, List[unicode])

        """
        OutStrings = []
        if Strings:
            if not isinstance(Strings, list):
                Strings = [Strings]
            for String in Strings:
                OutStrings.append("".join(ch for ch in unicode(
                    String) if unicodedata.category(ch)[0] != "C"))
        return OutStrings if isinstance(Strings, list) else OutStrings[0]

    @staticmethod
    def _NormalizeString(Context, Strings):
        """

        This function is available as an XPath function named 'ws_normalize', in
        the global namespace. It expects either a single string or a list of
        strings as input. It returns the input, stripping any leading or trailing
        white space. Also, multiple consecutive spaces are replaced with a single
        space. Example::

          'ws_normalize(string(./some/subtag))'

        Args:
            Context: lxml function context
            Strings (Union[unicode, List[unicode]): Input strings

        Returns:
          (Union[unicode, List[unicode])

        """
        OutStrings = []
        if Strings:
            if not isinstance(Strings, list):
                Strings = [Strings]
            for String in Strings:
                OutStrings.append(' '.join(String.split()))
        return OutStrings if isinstance(Strings, list) else OutStrings[0]

    def Generate(self, Element, XPathSelector, **kwargs):
        """

        Generates one or more EDXML events from the
        given XML element, populating it with properties
        using the XPATH_MAP class property.

        This method can be overridden to create a generic
        event generator, populating the output events with
        generic properties that may or may not be useful to
        the record specific transcoders. The record specific
        transcoders can refine the events that are generated
        upstream by adding, changing or removing properties,
        editing the event content, and so on.

        Args:
          Element (etree.Element): XML element
          XPathSelector (str): The matching XPath selector
          **kwargs: Arbitrary keyword arguments

        Yields:
          EDXMLEvent:
        """

        Properties = {}

        EventTypeName = self.TYPE_MAP.get(XPathSelector, None)

        for XPath, PropertyName in self.XPATH_MAP.items():

            if XPath not in XmlTranscoder._XPATH_MATCHERS:
                # Create and cache a compiled function for evaluating the
                # XPath expression.
                try:
                    XmlTranscoder._XPATH_MATCHERS[XPath] = etree.XPath(
                        XPath, namespaces={
                            're': 'http://exslt.org/regular-expressions'}
                    )
                except XPathSyntaxError:
                    raise ValueError(
                        'TYPE_MAP of %s contains invalid XPath for property %s: %s' % (
                            self.__class__, PropertyName, XPath)
                    )

            # Use the XPath evaluation function to find matches
            for Property in XmlTranscoder._XPATH_MATCHERS[XPath](Element):

                if PropertyName not in Properties:
                    Properties[PropertyName] = []
                try:
                    # Here, we assume that the XPath expression selects
                    # an XML tag. We will use its text to populate the property
                    if len(Property.text) == 0:
                        # Skip empty values
                        continue
                    elif Property.text in self.EMPTY_VALUES.get(XPath, ()):
                        # Property should be regarded as empty.
                        continue

                    Properties[PropertyName].append(unicode(Property.text))
                except AttributeError:
                    # Oops, XPath did not select a tag, it might be
                    # an attribute then.
                    Property = unicode(Property)
                    if len(Property) == 0:
                        # Skip empty values
                        continue
                    elif Property in self.EMPTY_VALUES.get(XPath, ()):
                        # Property should be regarded as empty.
                        continue
                    Properties[PropertyName].append(Property)
                except TypeError:
                    # XPath returned None
                    continue

        yield EventElement(Properties, EventTypeName)
