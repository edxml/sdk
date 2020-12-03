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
import unicodedata

from typing import Dict

import edxml.transcode

from edxml import EventElement
from lxml import etree
from lxml.etree import XPathSyntaxError


class XmlTranscoder(edxml.transcode.RecordTranscoder):

    TYPE_MAP = {}
    """
    The TYPE_MAP attribute is a dictionary mapping XPath expressions to EDXML
    event type names. The XPath expressions are relative to the XPath of the
    elements that that record transcoder is registered to at the transcoding mediator.
    The expressions in TYPE_MAP are evaluated on each XML input element to obtain
    sub-elements. For each sub-element an EDXML event of the corresponding type
    is generated. In case the events are supposed to be generated from the input
    element as a whole, you can use '.' for the XPath expression. However, you
    can also use the expressions to produce multiple types of output events
    from different parts of the input element.

    Note:
      When no EDXML event type name is specified for a particular XPath expression,
      it is up to the record transcoder to set the event type on the events that it generates.

    Note:
      The fallback transcoder must set the None key to the name of the EDXML
      fallback event type.

    Example:
        {'.': 'some-event-type'}
    """

    PROPERTY_MAP = {}
    """
    The PROPERTY_MAP attribute is a dictionary mapping event type names to the XPath
    expressions for finding property objects. Each value in the dictionary is another
    dictionary that maps property names to the XPath expression. The XPath expressions
    are relative to the source XML element of the event. Example::

        {'event-type-name': {'some/subtag[@attribute]': 'property-name'}}

    The use of EXSLT regular expressions is supported and may be used in Xpath keys
    like this::

        {'event-type-name': {'*[re:test(., "^abc$", "i")]': 'property-name'}}

    Mapping XPath expressions to multiple event properties is also possible::

        {'event-type-name': {'some/subtag[@attribute]': ['property', 'another-property']}}

    Extending XPath by injecting custom Python functions is supported due to the lxml
    implementation of XPath that is being used in the record transcoder implementation.
    Please refer to the lxml documentation about this subject. This record transcoder
    implementation provides a small set of custom XPath functions already, which shows
    how it is done.

    Note that the event structure will not be validated until the event is yielded by
    the generate() method. This creates the possibility to add nonexistent properties
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

    def __init__(self):
        super().__init__()

        self._xpath_matchers = {}  # type: Dict[str, etree.XPath]

        # TODO: It would be nicer to put functions into a
        # namespace, but lxml throws weird exceptions on repeated
        # invocations of namespaced functions...
        ns = etree.FunctionNamespace(None)
        ns['findall'] = XmlTranscoder._find_all
        ns['ctrl_strip'] = XmlTranscoder._strip_control_chars
        ns['ws_normalize'] = XmlTranscoder._normalize_string

    @staticmethod
    def _find_all(context, nodes, pattern, flags=0):
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
            context: lxml function context
            nodes (List[etree._Element]):
            Pattern Union[str, re.SRE_Pattern]:
            flags (int): Regular expression flags

        Returns:
          List[str]

        """
        total_matches = []
        for node in nodes:
            if node.text:
                matches = re.findall(pattern, node.text, int(flags))
                total_matches.extend(str(match) for match in matches)
        return total_matches

    @staticmethod
    def _strip_control_chars(context, strings):
        """

        This function is available as an XPath function named 'ctrl_strip', in
        the global namespace. It expects either a single string or a list of
        strings as input. It returns the input, stripping any control characters.
        Example::

          'ctrl_strip(string(./some/subtag))'

        Args:
            context: lxml function context
            strings (Union[str, List[str]): Input strings

        Returns:
          (Union[str, List[str])

        """
        out_strings = []
        if strings:
            for string in strings if isinstance(strings, list) else [str(strings)]:
                try:
                    # Try treating string as an XML element first.
                    out_strings.append("".join(ch for ch in str(string.text) if unicodedata.category(ch)[0] != "C"))
                except AttributeError:
                    # That did not work. It must be an attribute or
                    # an actual string then.
                    out_strings.append("".join(ch for ch in str(string) if unicodedata.category(ch)[0] != "C"))
        return out_strings if isinstance(strings, list) else out_strings[0]

    @staticmethod
    def _normalize_string(context, strings):
        """

        This function is available as an XPath function named 'ws_normalize', in
        the global namespace. It expects either a single string or a list of
        strings as input. It returns the input, stripping any leading or trailing
        white space. Also, multiple consecutive spaces are replaced with a single
        space. Example::

          'ws_normalize(string(./some/subtag))'

        Args:
            context: lxml function context
            strings (Union[str, List[str]): Input strings

        Returns:
          (Union[str, List[str])

        """
        out_strings = []
        if strings:
            for string in strings if isinstance(strings, list) else [str(strings)]:
                try:
                    out_strings.append(' '.join(string.split()))
                except AttributeError:
                    # If string is not a string then it must
                    # be an element.
                    out_strings.append(' '.join(string.text.split()))
        return out_strings if isinstance(strings, list) else out_strings[0]

    def generate(self, element, xpath_selector, **kwargs):
        """

        Generates one or more EDXML events from the
        given XML element, populating it with properties
        using the PROPERTY_MAP class property.

        When the record transcoder is the fallback transcoder,
        xpath_selector will be None.

        This method can be overridden to create a generic
        event generator, populating the output events with
        generic properties that may or may not be useful to
        the specific record transcoders. The specific record
        transcoders can refine the events that are generated
        upstream by adding, changing or removing properties,
        editing the event content, and so on.

        Args:
          element (etree.Element): XML element
          xpath_selector (Optional[str]): The matching XPath selector
          **kwargs: Arbitrary keyword arguments

        Yields:
          EDXMLEvent:
        """

        for event_type_xpath, event_type_name in self.TYPE_MAP.items():
            if event_type_xpath not in self._xpath_matchers:
                # Create and cache a compiled function for evaluating the
                # XPath expression.
                try:
                    self._xpath_matchers[event_type_xpath] = etree.XPath(
                        event_type_xpath, namespaces={
                            're': 'http://exslt.org/regular-expressions'}
                    )
                except XPathSyntaxError:
                    raise ValueError(
                        'TYPE_MAP of %s contains invalid XPath for event type %s: %s' % (
                            type(self).__name__, event_type_name, event_type_xpath)
                    )

            for sub_element in self._xpath_matchers[event_type_xpath](element):
                yield self._generate_event(event_type_name, sub_element)

    def _generate_event(self, event_type_name, element):

        properties = {}

        for xpath, property_names in self.PROPERTY_MAP[event_type_name].items():

            if not isinstance(property_names, list):
                property_names = [property_names]

            if xpath not in self._xpath_matchers:
                # Create and cache a compiled function for evaluating the
                # XPath expression.
                try:
                    self._xpath_matchers[xpath] = etree.XPath(
                        xpath, namespaces={
                            're': 'http://exslt.org/regular-expressions'}
                    )
                except XPathSyntaxError:
                    raise ValueError(
                        'PROPERTY_MAP of %s contains invalid XPath for property %s: %s' %
                        (type(self).__name__, ', '.join(property_names), xpath)
                    )

            # Use the XPath evaluation function to find matches
            for property in self._xpath_matchers[xpath](element):

                for property_name in [name for name in property_names if name not in properties]:
                    properties[property_name] = []
                try:
                    # Here, we assume that the XPath expression selects
                    # an XML tag. We will use its text to populate the property
                    if property.text is None:
                        # Skip empty values
                        continue
                    elif property.text in self.EMPTY_VALUES.get(xpath, ()):
                        # Property should be regarded as empty.
                        continue

                    for property_name in property_names:
                        properties[property_name].append(property.text)
                except AttributeError:
                    # Oops, XPath did not select a tag, it might be
                    # an attribute then.
                    property = str(property)
                    if property == '':
                        # Skip empty values
                        continue
                    elif property in self.EMPTY_VALUES.get(xpath, ()):
                        # Property should be regarded as empty.
                        continue
                    for property_name in property_names:
                        properties[property_name].append(property)

        return EventElement(self._post_process_properties(event_type_name, properties), event_type_name)
