# -*- coding: utf-8 -*-

import re
import hashlib


from collections import MutableMapping
from collections import defaultdict
from lxml import etree
from copy import deepcopy
from decimal import Decimal
from edxml.EDXMLBase import EvilCharacterFilter, EDXMLValidationError


class EDXMLEvent(MutableMapping):
    """Class representing an EDXML event.

    The event allows its properties to be accessed
    and set much like a dictionary:

        Event['property-name'] = 'value'

    Note:
      Properties are lists of object values. On assignment,
      non-list values are automatically wrapped into lists.

    """

    def __init__(self, properties, event_type_name=None, source_uri=None, parents=None, content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Args:
          properties (Dict[str,List[unicode]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          content (Optional[unicode]): Event content

        Returns:
          EDXMLEvent
        """
        self._properties = properties
        self._event_type_name = event_type_name
        self._source_uri = source_uri
        self._parents = set(parents) if parents is not None else set()
        self._content = unicode(content) if content else u''

    def __str__(self):
        return "\n".join(
            ['%20s:%s' % (property_name, ','.join([unicode(value) for value in values]))
             for property_name, values in self._properties.iteritems()]
        )

    def __delitem__(self, key):
        self._properties.pop(key, None)

    def __setitem__(self, key, value):
        if type(value) == list:
            self._properties[key] = value
        else:
            self._properties[key] = [value]

    def __len__(self):
        return len(self._properties)

    def __getitem__(self, key):
        try:
            return self._properties[key]
        except KeyError:
            return []

    def __contains__(self, key):
        try:
            self._properties[key][0]
        except (KeyError, IndexError):
            return False
        else:
            return True

    def __iter__(self):
        for property_name, objects in self._properties.items():
            yield property_name

    def get_any(self, property_name, default=None):
        """

        Convenience method for fetching any of possibly multiple
        object values of a specific event property. If the requested
        property has no object values, the specified default value
        is returned in stead.

        Args:
          property_name (string): Name of requested property
          default: Default return value

        Returns:

        """
        value = self.get(property_name)
        try:
            return value[0]
        except IndexError:
            return default

    def copy(self):
        """

        Returns a copy of the event.

        Returns:
           EDXMLEvent
        """
        return EDXMLEvent(self._properties.copy(), self._event_type_name, self._source_uri, list(self._parents),
                          self._content)

    @classmethod
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Note:
          For a slight performance gain, use the EDXMLEvent constructor
          directly to create new events.

        Args:
          properties (Dict[str,Union[unicode,List[unicode]]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          content (Optional[unicode]): Event content

        Returns:
          EDXMLEvent:
        """
        return cls(
            {property_name: value if type(value) == list else [
                value] for property_name, value in properties.items()},
            event_type_name,
            source_uri,
            parents,
            content
        )

    def get_type_name(self):
        """

        Returns the name of the event type.

        Returns:
          str: The event type name

        """
        return self._event_type_name

    def get_source_uri(self):
        """

        Returns the URI of the event source.

        Returns:
          str: The source URI

        """
        return self._source_uri

    def get_properties(self):
        """

        Returns a dictionary containing property names
        as keys. The values are lists of object values.

        Returns:
          Dict[str, List[unicode]]: Event properties

        """
        return self._properties

    def get_explicit_parents(self):
        """

        Returns a list of sticky hashes of parent
        events. The hashes are hex encoded strings.

        Returns:
          List[str]: List of parent hashes

        """
        return list(self._parents)

    def get_content(self):
        """

        Returns the content of the event.

        Returns:
          unicode: Event content

        """
        return self._content

    @classmethod
    def create_from_xml(cls, event_type_name, source_uri, event_element):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          event_type_name (str): The name of the event type
          source_uri (str): The URI of the EDXML event source
          event_element (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        content = ''
        property_objects = {}
        for element in event_element:
            if element.tag == 'properties':
                for property_element in element:
                    property_name = property_element.tag
                    if property_name not in property_objects:
                        property_objects[property_name] = []
                    property_objects[property_name].append(property_element.text)
            elif element.tag == 'content':
                content = element.text

        return cls(property_objects, event_type_name, source_uri, event_element.attrib.get('parents'), content)

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of unicode strings.

        Args:
          properties: Dict(str, List(unicode)): Event properties

        Returns:
          EDXMLEvent:

        """
        self._properties = properties
        return self

    def copy_properties_from(self, source_event, property_map):
        """

        Copies properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EDXMLEvent):
         property_map (dict(str,str)):

        Returns:
          EDXMLEvent:
        """

        for source, targets in property_map.iteritems():
            try:
                source_properties = source_event._properties[source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(source_properties) > 0:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self._properties:
                        self._properties[target] = []
                        self._properties[target].extend(source_properties)

        return self

    def move_properties_from(self, source_event, property_map):
        """

        Moves properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EDXMLEvent):
         property_map (dict(str,str)):

        Returns:
          EDXMLEvent:
        """

        for source, targets in property_map.iteritems():
            try:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self._properties:
                        self._properties[target] = []
                    self._properties[target].extend(
                        source_event._properties[source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del source_event._properties[source]

        return self

    def set_type(self, event_type_name):
        """

        Set the event type.

        Args:
          event_type_name (str): Name of the event type

        Returns:
          EDXMLEvent:
        """
        self._event_type_name = event_type_name
        return self

    def set_content(self, content):
        """

        Set the event content.

        Args:
          content (unicode): Content string

        Returns:
          EDXMLEvent:
        """
        self._content = content
        return self

    def set_source(self, source_uri):
        """

        Set the event source.

        Args:
          source_uri (str): EDXML source URI

        Returns:
          EDXMLEvent:
        """
        self._source_uri = source_uri
        return self

    def add_parents(self, parent_hashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          parent_hashes (List[str]): list of sticky hash, as hexadecimal strings

        Returns:
          EDXMLEvent:
        """
        self._parents.update(parent_hashes)
        return self

    def set_parents(self, parent_hashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          parent_hashes (List[str]): list of sticky hash, as hexadecimal strings

        Returns:
          EDXMLEvent:
        """
        self._parents = set(parent_hashes)
        return self

    def merge_with(self, colliding_events, ontology):
        """
        Merges the event with event data from a number of colliding
        events. It returns True when the event was updated
        as a result of the merge, returns False otherwise.

        Args:
          colliding_events (List[EDXMLEvent]): Iterable yielding events
          ontology (edxml.ontology.Ontology): The EDXML ontology

        Returns:
          bool: Event was changed or not

        """

        event_type = ontology.get_event_type(self._event_type_name)
        properties = event_type.get_properties()
        property_names = properties.keys()
        unique_properties = event_type.get_unique_properties()

        # There used to be a check here to count the number of unique properties and raise a TypeError if there were
        # none. However, if the properties of an event are not unique, and it collides with another event (i.e. produce
        # the same hash), they are the same. Merging them will result in the same event without any changes. We've
        # removed the check altogether and the testcases that come with this comment show that these kinds of events
        # can be merged without problems.
        # Even events which are not the same but have no unique properties can now be merged. This will change the
        # event data according to the normal merge strategies, and possibly the hash. This is outside of the spec
        # but may be useful for processors, e.g. for aggregation calculations. The results of such a merge should not
        # be considered a new valid event.

        event_objects_a = self.get_properties()

        # Below, we initialize three dictionaries containing
        # event object sets. All objects are complete, in the
        # sense that they contain a list of objects for each
        # of the defined properties of the event type, even
        # if the event has no objects for the property.
        #
        # The Original dict holds the original event, before
        # the merge.
        # The Target dict is what will eventually become the
        # new, merged event.
        # The source event holds all object values from all
        # source events.

        original = {}
        source = {}
        target = {}

        source_parents = set()

        for property_name in property_names:
            value = event_objects_a.get(property_name, [])
            # Note that we use separate sets for original, source and target properties.
            # Sets are objects and assigned by reference, while we want to change them independently.
            original[property_name] = set(value)
            target[property_name] = set(value)
            source[property_name] = set()
            for event in colliding_events:
                event_objects_b = event.get_properties()
                source[property_name].update(event_objects_b.get(property_name, []))
                source_parents.update(event.get_explicit_parents())

        value_functions = defaultdict(lambda: int)
        value_functions['datetime'] = lambda x: x
        value_functions['float'] = float
        value_functions['double'] = float
        value_functions['decimal'] = Decimal

        # Now we update the objects in Target
        # using the values in Source
        for property_name in source:

            if property_name in unique_properties:
                # Unique property, does not need to be merged.
                continue

            merge_strategy = properties[property_name].get_merge_strategy()

            if merge_strategy in ('min', 'max'):
                # We have a merge strategy that requires us to cast
                # the object values into numbers.
                split_data_type = properties[property_name].get_data_type().get_split()
                if split_data_type[0] in ('number', 'datetime'):
                    if merge_strategy in ('min', 'max'):
                        values = set()
                        if split_data_type[0] == 'datetime':
                            # Note that we add the datetime values as
                            # regular strings and just let min() and max()
                            # use lexicographical sorting to determine which
                            # of the datetime values to pick.
                            value_func = value_functions[split_data_type[0]]
                        else:
                            value_func = value_functions[split_data_type[1]]
                        # convert values according to their data type and add to the result
                        values.update(map(value_func, source[property_name] | target[property_name]))

                        if merge_strategy == 'min':
                            target[property_name] = {str(min(values))}
                        else:
                            target[property_name] = {str(max(values))}

            elif merge_strategy == 'add':
                target[property_name].update(source[property_name])

            elif merge_strategy == 'replace':
                # Replace the property with the last value in the colliding events
                target[property_name] = set(colliding_events[-1].get(property_name, []))

        # Merge the explicit event parents
        original_parents = set(self.get_explicit_parents())
        # We no longer check for empty sets because setting it again has the same effect
        self.set_parents(original_parents | source_parents)

        # Determine if anything changed
        event_updated = target != original
        event_updated |= original_parents != source_parents

        # Modify event if needed
        self.set_properties(target)
        return event_updated

    def compute_sticky_hash(self, ontology, encoding='hex'):
        """

        Computes the sticky hash of the event. By default, the hash
        will be encoded into a hexadecimal string. The encoding can
        be adjusted by setting the encoding argument to any string
        encoding that is supported by the str.encode() method.

        Args:
          ontology (edxml.ontology.Ontology): An EDXML ontology
          encoding (str): Desired output encoding

        Note:
          The object values of the event must be valid EDXML object value strings or
          values that can be cast to valid EDXML object value strings.

        Returns:
          str: String representation of the hash.

        """

        event_type = ontology.get_event_type(self._event_type_name)
        objects = self.get_properties()
        hash_properties = event_type.get_hash_properties()

        object_strings = set('%s:%s' % (p, v)
                             for p in objects if p in hash_properties for v in objects[p])

        # Now we compute the SHA1 hash value of the byte
        # string representation of the event, and output in hex

        if event_type.is_unique():
            return hashlib.sha1(
                '%s\n%s\n%s' % (self._source_uri, self._event_type_name,
                                '\n'.join(sorted(object_strings)))
            ).digest().encode(encoding)
        else:
            return hashlib.sha1(
                '%s\n%s\n%s\n%s' % (self._source_uri, self._event_type_name, '\n'.join(
                    sorted(object_strings)), self.get_content())
            ).digest().encode(encoding)

    def is_valid(self, ontology):
        """
        Check if an event is valid for a given ontology.

        Args:
            ontology (edxml.ontology.Ontology): An EDXML ontology

        Returns:
            bool: True if the event is valid
        """
        event_type = ontology.get_event_type(self.get_type_name())

        if event_type is None:
            return False

        try:
            event_type.validate_event_structure(self)
            event_type.validate_event_objects(self)
        except EDXMLValidationError:
            return False
        return True


class ParsedEvent(EDXMLEvent, EvilCharacterFilter, etree.ElementBase):
    """
    This class extends both EDXMLEvent and etree.ElementBase to
    provide an EDXML event representation that can be generated directly
    by the lxml parser and can be treated much like it was a normal
    lxml Element representing an 'event' element

    Note:
      The list and dictionary interfaces of etree.ElementBase are
      overridden by EDXMLEvent, so accessing keys will yield event properties
      rather than the XML attributes of the event element.

    Note:
      This class can only be instantiated by parsers.

    """

    def __str__(self):
        return etree.tostring(self)

    def __delitem__(self, key):
        props = self.find('properties')
        for element in props.findall(key):
            props.remove(element)
        try:
            del self._properties
        except AttributeError:
            pass

    def __setitem__(self, key, value):
        if type(value) == list:
            props = self.find('properties')
            for existing_value in props.findall(key):
                props.remove(existing_value)
            for v in value:
                try:
                    etree.SubElement(props, key).text = v
                except (TypeError, ValueError):
                    if type(v) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        props[-1].text = unicode(
                            re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), v))
                    else:
                        raise ValueError(
                            'Value of property %s is not a string: %s' % (key, repr(value)))
        else:
            props = self.find('properties')
            for existing_value in props.findall(key):
                props.remove(existing_value)
            try:
                etree.SubElement(props, key).text = value
            except (TypeError, ValueError):
                if type(value) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    props[-1].text = unicode(
                        re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), value))
                else:
                    raise ValueError(
                        'Value of property %s is not a string: %s' % (key, repr(value)))
        try:
            del self._properties
        except AttributeError:
            pass

    def __len__(self):
        try:
            return len(self._properties)
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.find('properties'):
                self._properties[element.tag].append(element.text)
            return len(self._properties)

    def __getitem__(self, key):
        try:
            return self._properties[key]
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.find('properties'):
                self._properties[element.tag].append(element.text)
            return self._properties[key]

    def __contains__(self, key):
        try:
            return key in self._properties
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.find('properties'):
                self._properties[element.tag].append(element.text)
            return key in self._properties

    def __iter__(self):
        try:
            for p in self._properties.keys():
                yield p
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.find('properties'):
                self._properties[element.tag].append(element.text)
            for p in self._properties.keys():
                yield p

    def flush(self):
        """

        This class caches an alternative representation of
        the lxml Element, for internal use. Whenever the
        lxml Element is modified without using the dictionary
        interface, the flush() method must be called in order
        to refresh the internal state.

        Returns:
          ParsedEvent:
        """
        try:
            del self._properties
        except AttributeError:
            pass

        return self

    def copy(self):
        """

        Returns a copy of the event.

        Returns:
           ParsedEvent:
        """
        return deepcopy(self)

    @classmethod
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, content=None):
        """

        This override of the create() method of the EDXMLEvent class
        only raises exceptions, because ParsedEvent objects can only
        be created by parsers.

        Raises:
          NotImplementedError

        """
        raise NotImplementedError(
            'ParsedEvent objects can only be created by parsers')

    @classmethod
    def create_from_xml(cls, event_type_name, source_uri, event_element):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          event_type_name (str): The name of the event type
          source_uri (str): The URI of the EDXML event source
          event_element (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        content = ''
        property_objects = {}
        for element in event_element:
            if element.tag == 'properties':
                for property_element in element:
                    property_name = property_element.tag
                    if property_name not in property_objects:
                        property_objects[property_name] = []
                    property_objects[property_name].append(property_element.text)
            elif element.tag == 'content':
                content = element.text

        return cls(property_objects, event_type_name, source_uri, event_element.attrib.get('parents'), content)

    def get_properties(self):
        try:
            return self._properties
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.find('properties'):
                self._properties[element.tag].append(element.text)
            return self._properties

    def get_content(self):
        try:
            return self.find('content').text
        except AttributeError:
            return ''

    def get_explicit_parents(self):
        try:
            return self.attrib['parents'].split(',')
        except KeyError:
            return []

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of unicode strings.

        Args:
          properties: Dict(str, List(unicode)): Event properties

        Returns:
          EDXMLEvent:

        """
        properties_element = self.find('properties')
        properties_element.clear()

        for property_name, values in properties.items():
            for value in values:
                etree.SubElement(properties_element, property_name).text = value

        try:
            del self._properties
        except AttributeError:
            pass

        return self

    def copy_properties_from(self, source_event, property_map):
        """

        Copies properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EDXMLEvent): Source event
         property_map (Dict[str,str]): Property mapping

        Returns:
          EDXMLEvent:
        """

        for source, targets in property_map.iteritems():
            try:
                source_properties = source_event._properties[source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(source_properties) > 0:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self:
                        self[target] = []
                    self[target].extend(source_properties)

        return self

    def move_properties_from(self, source_event, property_map):
        """

        Moves properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EDXMLEvent): Source event
         property_map (Dict[str,str]): Property mapping

        Returns:
          EDXMLEvent:
        """

        for source, targets in property_map.iteritems():
            try:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self._properties:
                        self[target] = []
                    self[target].extend(source_event._properties[source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del source_event[source]

        return self

    def set_content(self, content):
        """

        Set the event content.

        Args:
          content (unicode): Content string

        Returns:
          ParsedEvent:
        """
        try:
            self.find('content').text = content
        except (TypeError, ValueError):
            if type(content) in (str, unicode):
                # Value contains illegal characters,
                # replace them with unicode replacement characters.
                self.find('content').text = unicode(
                    re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), content))
            else:
                raise ValueError(
                    'Event content value is not a string: %s' % repr(content))
        return self

    def add_parents(self, parent_hashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          ParsedEvent:
        """
        self.attrib.set('parents', ','.join(self.attrib.get(
            'parents').split(',').append(parent_hashes)))
        return self

    def set_parents(self, parent_hashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          ParsedEvent:
        """
        self.attrib.set('parents', ','.join(parent_hashes))
        return self


class EventElement(EDXMLEvent, EvilCharacterFilter):
    """
    This class extends EDXMLEvent to provide an EDXML event representation
    that wraps an etree Element instance, providing a convenient means to
    generate and manipulate EDXML <event> elements. Using this class is
    preferred over using EDXMLEvent if you intend to feed it to EDXMLWriter
    or SimpleEDXMLWriter.
    """

    def __init__(self, properties, event_type_name=None, source_uri=None, parents=None, content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple unicode strings. Explicit parent
        hashes must be specified as hex encoded strings.

        Args:
          properties (Dict(str, List[unicode])): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[optional]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          content (Optional[unicode]): Event content

        Returns:
          EventElement:
        """
        super(EventElement, self).__init__(properties,
                                           event_type_name, source_uri, parents, content)

        # These are now kept in an etree element.
        self._properties = None
        self._parents = None
        self._content = None

        new = etree.Element('event')
        if parents:
            new.set('parents', ','.join(parents))

        p = etree.SubElement(new, 'properties')
        for property_name, values in properties.iteritems():
            for value in values:
                try:
                    etree.SubElement(p, property_name).text = value
                except (TypeError, ValueError):
                    if type(value) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        char_filter = EvilCharacterFilter()
                        p[-1].text = unicode(
                            re.sub(char_filter.evil_xml_chars_regexp, unichr(0xfffd), value))
                    else:
                        raise ValueError(
                            'Object value is not a string: ' + repr(value))
        if content:
            try:
                etree.SubElement(new, 'content').text = content
            except (TypeError, ValueError):
                if type(content) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    char_filter = EvilCharacterFilter()
                    new[-1].text = unicode(
                        re.sub(char_filter.evil_xml_chars_regexp, unichr(0xfffd), content))
                else:
                    raise ValueError(
                        'Event content is not a string: ' + repr(content))

        self.__element = new
        self._properties = None

    def __str__(self):
        return etree.tostring(self.__element)

    def __delitem__(self, key):
        props = self.__element.find('properties')
        for element in props.findall(key):
            props.remove(element)
        self._properties = None

    def __setitem__(self, key, value):
        if type(value) == list:
            props = self.__element.find('properties')
            for existing_value in props.findall(key):
                props.remove(existing_value)
            for v in set(value):
                try:
                    etree.SubElement(props, key).text = v
                except (TypeError, ValueError):
                    if type(v) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        props[-1].text = unicode(
                            re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), v))
                    else:
                        raise ValueError(
                            'Value of property %s is not a string: %s' % (key, repr(value)))
        else:
            props = self.__element.find('properties')
            for existing_value in props.findall(key):
                props.remove(existing_value)
            try:
                etree.SubElement(props, key).text = value
            except (TypeError, ValueError):
                if type(value) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    props[-1].text = unicode(
                        re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), value))
                else:
                    raise ValueError(
                        'Value of property %s is not a string: %s' % (key, repr(value)))
        self._properties = None

    def __len__(self):
        try:
            return len(self._properties)
        except TypeError:
            self._properties = defaultdict(list)
            for element in self.__element.find('properties'):
                self._properties[element.tag].append(element.text)
            return len(self._properties)

    def __getitem__(self, key):
        try:
            return self._properties[key]
        except TypeError:
            self._properties = defaultdict(list)
            for element in self.__element.find('properties'):
                self._properties[element.tag].append(element.text)
            return self._properties[key]

    def __contains__(self, key):
        try:
            return key in self._properties
        except TypeError:
            self._properties = defaultdict(list)
            for element in self.__element.find('properties'):
                self._properties[element.tag].append(element.text)
            return key in self._properties

    def __iter__(self):
        try:
            for p in self._properties.keys():
                yield p
        except AttributeError:
            self._properties = defaultdict(list)
            for element in self.__element.find('properties'):
                self._properties[element.tag].append(element.text)
            for p in self._properties.keys():
                yield p

    def get_element(self):
        return self.__element

    def copy(self):
        """

        Returns a copy of the event.

        Returns:
           EventElement:
        """
        return deepcopy(self)

    @classmethod
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Note:
          For a slight performance gain, use the EventElement constructor
          directly to create new events.

        Args:
          properties (Dict[str,Union[unicode,List[unicode]]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          content (Optional[unicode]): Event content

        Returns:
          EventElement:
        """
        return cls(
            {property_name: value if type(value) == list else [
                value] for property_name, value in properties.items()},
            event_type_name,
            source_uri,
            parents,
            content
        )

    @classmethod
    def create_from_xml(cls, event_type_name, source_uri, event_element):
        """

        Creates and returns a new EventElement instance by reading it from
        specified lxml Element instance.

        Args:
          event_type_name (str): The name of the event type
          source_uri (str): The URI of the EDXML event source
          event_element (etree.Element): The XML element containing the event

        Returns:
          EventElement:
        """

        new = cls({})
        new.__element = event_element

        return new

    def get_properties(self):
        try:
            return dict(self._properties)
        except TypeError:
            self._properties = defaultdict(list)
            for element in self.__element.find('properties'):
                self._properties[element.tag].append(element.text)
            return self._properties

    def get_content(self):
        try:
            return self.__element.find('content').text
        except AttributeError:
            # No content.
            return ''

    def get_explicit_parents(self):
        try:
            return self.__element.attrib['parents'].split(',')
        except KeyError:
            return []

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of unicode strings.

        Args:
          properties: Dict(str, List(unicode)): Event properties

        Returns:
          EventElement:

        """
        properties_element = self.__element.find('properties')
        properties_element.clear()

        for property_name, values in properties.items():
            for value in values:
                try:
                    etree.SubElement(properties_element,
                                     property_name).text = value
                except (TypeError, ValueError):
                    if type(value) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        properties_element[-1].text = unicode(
                            re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), value))
                    else:
                        raise ValueError('Value of property %s is not a string: %s' % (
                            property_name, repr(value)))

        self._properties = None

        return self

    def copy_properties_from(self, source_event, property_map):
        """

        Copies properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EventElement): Source event
         property_map (Dict[str,str]): Property mapping

        Returns:
          EventElement:
        """

        for source, targets in property_map.iteritems():
            try:
                source_properties = source_event._properties[source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(source_properties) > 0:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self:
                        self[target] = []
                    self[target].extend(source_properties)

        return self

    def move_properties_from(self, source_event, property_map):
        """

        Moves properties from another event, mapping property names
        according to specified mapping. The PropertyMap argument is
        a dictionary mapping property names from the source event
        to property names in the target event, which is the event that
        is used to call this method.

        If multiple source properties map to the same target property,
        the objects of both properties will be combined in the target
        property.

        Args:
         source_event (EventElement): Source event
         property_map (Dict[str,str]): Property mapping

        Returns:
          EventElement:
        """

        for source, targets in property_map.iteritems():
            try:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in self._properties:
                        self[target] = []
                    self[target].extend(source_event._properties[source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del source_event[source]

        return self

    def set_content(self, content):
        """

        Set the event content.

        Args:
          content (unicode): Content string

        Returns:
          EventElement:
        """
        try:
            self.__element.find('content').text = content
        except AttributeError:
            etree.SubElement(self.__element, 'content').text = content
        except (TypeError, ValueError):
            if type(content) in (str, unicode):
                # Value contains illegal characters,
                # replace them with unicode replacement characters.
                self.__element.find('content').text = unicode(
                    re.sub(self.evil_xml_chars_regexp, unichr(0xfffd), content))
            else:
                raise ValueError(
                    'Event content value is not a string: %s' % repr(content))
        return self

    def add_parents(self, parent_hashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          EventElement:
        """
        self.__element.attrib.set('parents', ','.join(
            self.__element.attrib.get('parents').split(',').append(parent_hashes)))
        return self

    def set_parents(self, parent_hashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          EventElement:
        """
        self.__element.attrib.set('parents', ','.join(parent_hashes))
        return self
