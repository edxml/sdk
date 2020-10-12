# -*- coding: utf-8 -*-
import codecs
import re
import hashlib
import sys

from collections.abc import MutableMapping, MutableSet
from collections import OrderedDict
from datetime import datetime
from IPy import IP
from lxml import etree
from copy import deepcopy

from edxml.error import EDXMLValidationError
from edxml.ontology import DataType


# The lxml package does not filter out illegal XML
# characters. So, below we compile a regular expression
# matching all ranges of illegal characters. We will
# use that to do our own filtering.
def get_evil_chars():

    ranges = [
        (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
        (0x7F, 0x84), (0x86, 0x9F),
        (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)
    ]

    if sys.maxunicode >= 0x10000:  # not narrow build
        ranges.extend([
            (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
            (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
            (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
            (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
            (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
            (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
            (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
            (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)
        ])

    return '[%s]' % ''.join(
        ["%s-%s" % (chr(low), chr(high)) for (low, high) in ranges]
    )


EVIL_XML_CHARS_REGEXP = get_evil_chars()


def to_edxml_object(property_name, value):
    """
    Function to coerce values of various types
    into their native EDXML string representations.

    Args:
        property_name (str):
        value:

    Returns:
        str:
    """
    if isinstance(value, IP):
        return value.strFullsize()
    elif isinstance(value, datetime):
        return DataType.format_utc_datetime(value)
    elif type(value) in (int, float):
        return str(value)
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, bytes):
        return value.decode('utf-8')
    else:
        raise ValueError(
            'Value of property %s is not a string: %s' % (property_name, repr(value))
        )


class PropertySet(OrderedDict):
    def __init__(self, properties=None, update_property=None):
        super().__init__()
        if properties is not None:
            for property_name, values in properties.items() or {}:
                super().__setitem__(property_name, PropertyObjectSet(property_name, values, update_property))

        if update_property is not None:
            self._update_property = update_property

    def _update_property(self, property_name, values):
        pass

    def replace_object_set(self, property_name, object_set):
        super().__setitem__(property_name, object_set)

    def items(self):
        return [(key, values) for key, values in super().items() if len(values) > 0]

    def keys(self):
        return [key for key, values in super().items() if len(values) > 0]

    def __iter__(self):
        for p, objects in super().items():
            if len(objects) > 0:
                yield p

    def __len__(self):
        return len(self.keys())

    def __eq__(self, other):
        return dict(other) == {p: v for p, v in super().items() if len(v) > 0}

    def __contains__(self, item):
        return item in super().keys() and len(super().__getitem__(item)) > 0

    def __setitem__(self, key, value):
        super().__setitem__(key, PropertyObjectSet(key, value, self._update_property))
        self._update_property(key, value)

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            if not isinstance(item, str):
                raise TypeError('Property name is not a string: ' + repr(item))
            super().__setitem__(item, PropertyObjectSet(item, update=self._update_property))
            return super().__getitem__(item)

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
            self._update_property(key, None)
        except KeyError:
            pass

    def __deepcopy__(self, memodict=None):
        return PropertySet(dict(self), update_property=self._update_property)


class PropertyObjectSet(set, MutableSet):
    def __init__(self, property_name, objects=None, update=None):
        super().__init__()
        if property_name is None:
            raise ValueError()
        self.__property_name = property_name
        if isinstance(objects, set):
            self.update(objects)
        else:
            if isinstance(objects, (str, int, bool, float, datetime, IP)):
                objects = (objects,)
            self.update(set(iter(objects or [])))
        if update is not None:
            self._update = update

    def __deepcopy__(self, memodict=None):
        return PropertyObjectSet(self.__property_name, [deepcopy(v) for v in self], self._update)

    def __eq__(self, other):
        return set(self) == other

    def add(self, value):
        super().add(value)
        self._update(self.__property_name, self)

    def remove(self, element):
        super().remove(element)
        self._update(self.__property_name, self)

    def update(self, values):
        super().update(values)
        self._update(self.__property_name, self)

    def clear(self):
        super().clear()
        self._update(self.__property_name, self)

    def discard(self, element):
        super().discard(element)
        self._update(self.__property_name, self)

    def pop(self):
        super().pop()
        self._update(self.__property_name, self)

    def _update(self, property_name, values):
        pass


class AttachmentSet(OrderedDict):
    def __init__(self, attachments=None, update_attachment=None):
        super().__init__()
        if attachments is not None:
            for attachment_name, value in attachments.items() or {}:
                try:
                    self[attachment_name] = '' + value
                except TypeError as e:
                    raise TypeError(f"Failed to set event attachment {attachment_name}: {e}")

        if update_attachment is not None:
            self._update_attachment = update_attachment

    def _update_attachment(self, attachment_name, value):
        pass

    def __iter__(self):
        for name, value in super().items():
            if len(value) > 0:
                yield name

    def __eq__(self, other):
        return other == {a: v for a, v in super().items() if len(v) > 0}

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._update_attachment(key, value)

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            self[item] = ''
            return self[item]

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
            self._update_attachment(key, None)
        except KeyError:
            pass


class EDXMLEvent(MutableMapping):
    """Class representing an EDXML event.

    The event allows its properties to be accessed
    and set much like a dictionary:

        Event['property-name'] = 'value'

    Note:
      Properties are lists of object values. On assignment,
      non-list values are automatically wrapped into lists.

    """

    def __init__(self, properties, event_type_name=None, source_uri=None, parents=None, attachments=None,
                 foreign_attribs=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Attachments are specified by means of a dictionary mapping attachment
        names to strings.

        Args:
          properties (Dict[str,Set[str]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          attachments (Optional[Dict[str, str]]): Event attachments dictionary
          foreign_attribs (Optional[Dict[str, str]]) Foreign attributes dictionary

        Returns:
          EDXMLEvent
        """
        self._properties = None
        self._attachments = None
        self._event_type_name = event_type_name
        self._source_uri = source_uri
        self._parents = set(parents) if parents is not None else set()
        self._foreign_attribs = foreign_attribs if foreign_attribs is not None else {}

        self.set_properties(properties)
        self.set_attachments(attachments or {})

        self._replace_invalid_characters = False

    def __update_property(self, key, value): ...

    def __update_attachment(self, attachment_name, value): ...

    def __repr__(self):
        return f"Event of type {self.get_type_name()} from {self.get_source_uri()}"

    def __str__(self):
        return "\n".join(
            ['%20s:%s' % (property_name, ','.join(values))
             for property_name, values in self._properties.items()]
        )

    def __delitem__(self, key):
        del self._properties[key]

    def __setitem__(self, key, value):
        self._properties[key] = PropertyObjectSet(key, value)

    def __len__(self):
        return len(self._properties)

    def __getitem__(self, key):
        try:
            return self._properties[key]
        except KeyError:
            self._properties[key] = PropertyObjectSet(key)
            return self._properties[key]

    def __contains__(self, key):
        try:
            return len(self._properties[key]) > 0
        except (KeyError, IndexError):
            return False

    def __iter__(self):
        for property_name in self._properties:
            yield property_name

    def __eq__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Can only compare events to other events.")

        if self.get_type_name() != other.get_type_name():
            return False

        if self.get_source_uri() != other.get_source_uri():
            return False

        if not self.properties.__eq__(other.properties):
            return False

        if self.attachments != other.attachments:
            return False

        if set(self.get_explicit_parents()) != set(other.get_explicit_parents()):
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def replace_invalid_characters(self, replace=True):
        """
        Enables automatic replacement of invalid unicode characters with
        the unicode replacement character. This will be used to produce
        valid XML representations of events containing invalid unicode
        characters in their property objects or attachments.

        Enabling this feature may be useful when dealing with broken input
        data that triggers an occasional ValueError. In stead of crashing,
        the invalid data will be automatically replaced.

        Args:
            replace (bool):

        Returns:
            edxml.EDXMLEvent

        """
        self._replace_invalid_characters = replace
        return self

    @property
    def properties(self):
        return self.get_properties()

    @properties.setter
    def properties(self, new_properties):
        self.set_properties(new_properties)

    @property
    def attachments(self):
        """

        Class property storing the attachments of the event.

        Returns:
            Dict[str, str]
        """
        return self.get_attachments()

    @attachments.setter
    def attachments(self, new_attachments):
        """
        Setter for the event attachments dictionary

        Args:
            new_attachments (Dict[str, str]):
        """
        self.set_attachments(new_attachments)

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
            return list(value)[0]
        except IndexError:
            return default

    def get_element(self):
        return EventElement.create_from_event(self)\
            .replace_invalid_characters(self._replace_invalid_characters)\
            .get_element()

    def copy(self):
        """

        Returns a copy of the event.

        Returns:
           EDXMLEvent
        """
        return EDXMLEvent(
            self._properties.copy(),
            self._event_type_name,
            self._source_uri,
            list(self._parents),
            self._attachments.copy(),
            self._foreign_attribs
        )

    @classmethod
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, attachments=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Attachments are specified by means of a dictionary mapping attachment
        names to strings.

        Note:
          For a slight performance gain, use the EDXMLEvent constructor
          directly to create new events.

        Args:
          properties (Dict[str,Union[str,List[str]]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          attachments (Optional[str]): Event attachments dictionary

        Returns:
          EDXMLEvent:
        """
        return cls(
            properties,
            event_type_name,
            source_uri,
            parents,
            attachments
        )

    def sort(self):
        """

        Sorts the event properties and attachments on their names. This can be helpful when
        comparing differences between events.

        Returns:
            EDXMLEvent:
        """
        self._properties = PropertySet(OrderedDict(sorted(self._properties.items(), key=lambda t: t[0])))
        self._attachments = AttachmentSet(OrderedDict(sorted(self._attachments.items(), key=lambda t: t[0])))
        return self

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
          PropertySet: Event properties

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

    def get_attachments(self):
        """

        Returns the attachments of the event as a dictionary mapping
        attachment names to the attachment values

        Returns:
          Dict[str, str]: Event attachments

        """
        return self._attachments

    def get_foreign_attributes(self):
        """
        Returns any non-edxml event attributes as a dictionary having
        the attribute names as keys and their associated values. The
        namespace is prepended to the keys in James Clark notation:

        {'{http://some/foreign/namespace}attribute': 'value'

        Returns: Dict[str, str]

        """
        return self._foreign_attribs

    @classmethod
    def create_from_xml(cls, event_element):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          event_element (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        try:
            event_type_name = event_element.attrib["event-type"]
            source_uri = event_element.attrib["source-uri"]

            attachments = {}
            property_objects = {}
            for element in event_element:
                if element.tag == 'properties':
                    for property_element in element:
                        property_name = property_element.tag
                        if property_name not in property_objects:
                            property_objects[property_name] = set()
                        property_objects[property_name].add(property_element.text)
                elif element.tag == '{http://edxml.org/edxml}properties':
                    for property_element in element:
                        property_name = property_element.tag[24:]
                        if property_name not in property_objects:
                            property_objects[property_name] = set()
                        property_objects[property_name].add(property_element.text)
                elif element.tag == 'attachments':
                    for attachment in element:
                        attachments[attachment.tag] = attachment.text
                elif element.tag == '{http://edxml.org/edxml}attachments':
                    for attachment in element:
                        attachments[attachment.tag[24:]] = attachment.text

            return cls(property_objects, event_type_name, source_uri, event_element.attrib.get('parents'), attachments)

        except (ValueError, KeyError) as e:
            raise EDXMLValidationError(
                "Failed to instantiate an EDXML event from the following definition:\n" +
                etree.tostring(event_element, pretty_print=True, encoding='unicode') +
                "\nError message: " + str(e)
            )

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of strings.

        Args:
          properties: Dict(str, List(str)): Event properties

        Returns:
          EDXMLEvent:

        """
        self._properties = PropertySet(properties)
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

        props = self.get_properties()
        for source, targets in property_map.items():
            try:
                source_properties = source_event._properties[source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(source_properties) > 0:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if target not in props:
                        props[target] = PropertyObjectSet(target)
                    props[target].update(source_properties)

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

        props = self.get_properties()
        for source, targets in property_map.items():
            try:
                for target in (targets if isinstance(targets, list) else [targets]):
                    if source not in source_event:
                        continue
                    if target not in props:
                        props[target] = PropertyObjectSet(target)
                    props[target].update(source_event[source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del source_event[source]

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

    def set_attachments(self, attachments):
        """

        Set the event attachments. Attachments are specified
        as a dictionary mapping attachment names to strings.

        Args:
          attachments (Dict[str, str]): Attachment dictionary

        Returns:
          EDXMLEvent:
        """
        self._attachments = AttachmentSet(attachments)
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

    def set_foreign_attributes(self, attribs):
        """

        Sets foreign attributes. Foreign attributes are XML attributes
        not specified by EDXML and have a namespace that is not the
        EDXML namespace. The attributes can be passed as a dictionary.
        The keys in the dictionary must include the namespace in James
        Clark notation. Example:

        {'{http://some/namespace}attribute_name': 'attribute_value'}

        Args:
            attribs (Dict[str,str]): Attribute dictionary

        Returns:
          EDXMLEvent:
        """
        self._foreign_attribs = attribs
        return self

    def compute_sticky_hash(self, event_type, encoding='hex'):
        """

        Computes the sticky hash of the event. By default, the hash
        will be encoded into a hexadecimal string. The encoding can
        be adjusted by setting the encoding argument to any string
        encoding that is supported by the str.encode() method.

        Args:
          event_type (edxml.ontology.EventType): The event type
          encoding (str): Desired output encoding

        Returns:
          str: String representation of the hash.

        """

        object_separator = b'\xff\xff\xff\xff'

        objects = self.get_properties()
        hash_properties = event_type.get_hash_properties()

        object_strings = set(('%s:%s' % (p, v)).encode() for p in objects if p in hash_properties for v in objects[p])

        # Now we compute the SHA1 hash value of the byte
        # string representation of the event, and output in hex

        return codecs.encode(hashlib.sha1(
            (
                b'%s\n%s\n%s' % (
                    self.get_source_uri().encode(),
                    self.get_type_name().encode(),
                    object_separator.join(sorted(object_strings))
                )
            )
        ).digest(), encoding).decode()

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
            event_type.validate_event_attachments(self)
        except EDXMLValidationError:
            return False
        return True


class ParsedEvent(EDXMLEvent, etree.ElementBase):
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

    def __init__(self, properties, event_type_name=None, source_uri=None, parents=None, attachments=None,
                 foreign_attribs=None):
        super().__init__(properties, event_type_name, source_uri, parents, attachments, foreign_attribs)
        raise NotImplementedError('ParsedEvent objects can only be created by parsers')

    def __str__(self):
        return etree.tostring(self, encoding='unicode')

    def __delitem__(self, key):
        props = self.find('{http://edxml.org/edxml}properties')
        for element in props.findall('{http://edxml.org/edxml}' + key):
            props.remove(element)
        try:
            del self._properties
        except AttributeError:
            pass

    def __setitem__(self, key, value):
        object_set = PropertyObjectSet(key, value, update=self.__update_property)
        self.__update_property(key, object_set)
        try:
            self._properties.replace_object_set(key, object_set)
        except AttributeError:
            properties = self.get_properties()
            properties[key] = object_set
            self._properties = PropertySet(properties, update_property=self.__update_property)

    def __update_property(self, key, value):
        props = self.find('{http://edxml.org/edxml}properties')
        for existing_value in props.findall('{http://edxml.org/edxml}' + key):
            props.remove(existing_value)
        for v in value:
            try:
                etree.SubElement(props, '{http://edxml.org/edxml}' + key).text = v
            except (TypeError, ValueError):
                if isinstance(v, str):
                    # Value contains illegal characters.
                    if not getattr(self, '_replace_invalid_characters', False):
                        raise
                    # Replace illegal characters with unicode replacement characters.
                    props[-1].text = re.sub(EVIL_XML_CHARS_REGEXP, chr(0xfffd), v)
                else:
                    props[-1].text = to_edxml_object(key, v)

    def __update_attachment(self, attachment_name, value):
        attachments_element = self.find('{http://edxml.org/edxml}attachments')
        if attachments_element is None:
            attachments_element = etree.SubElement(self, '{http://edxml.org/edxml}attachments')

        existing_attachment = attachments_element.find('{http://edxml.org/edxml}' + attachment_name)
        if existing_attachment is not None:
            attachments_element.remove(existing_attachment)

        if value is None:
            return

        try:
            etree.SubElement(attachments_element, '{http://edxml.org/edxml}' + attachment_name).text = value
        except (TypeError, ValueError):
            if isinstance(value, str):
                # Value contains illegal characters.
                if not getattr(self, '_replace_invalid_characters', False):
                    raise
                # Replace illegal characters with unicode replacement characters.
                attachments_element[-1].text = re.sub(EVIL_XML_CHARS_REGEXP, chr(0xfffd), value)
            else:
                attachments_element[-1].text = value

    def __len__(self):
        return len(self.get_properties())

    def __getitem__(self, key):
        return self.get_properties()[key]

    def __contains__(self, key):
        return key in self.get_properties()

    def __iter__(self):
        for p in self.get_properties().keys():
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
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, attachments=None):
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
    def create_from_xml(cls, event_element):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          event_element (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        # Below is a limitation of the lxml library.
        raise NotImplementedError('ParsedEvent can only be instantiated by EDXML parsers.')

    def sort(self):
        """

        Sorts the event properties and attachments on their names. This can be helpful when
        comparing differences between events.

        Returns:
            EDXMLEvent:
        """
        props = self.find('{http://edxml.org/edxml}properties')
        if props is not None:
            props[:] = sorted(props, key=lambda element: (element.tag, element.text))
            try:
                del self._properties
            except AttributeError:
                pass

        attachments = self.find('{http://edxml.org/edxml}attachments')
        if attachments is not None:
            attachments[:] = sorted(attachments, key=lambda element: (element.tag, element.text))
            try:
                del self._attachments
            except AttributeError:
                pass

        return self

    def get_properties(self):
        try:
            return self._properties
        except AttributeError:
            properties = OrderedDict()
            for element in self.find('{http://edxml.org/edxml}properties'):
                tag = element.tag[24:]
                if tag not in properties:
                    properties[tag] = set()
                properties[tag].add(element.text)

            self._properties = PropertySet(
                properties, update_property=self.__update_property
            )

            return self._properties

    def get_attachments(self):
        try:
            return self._attachments
        except AttributeError:
            attachments_element = self.find('{http://edxml.org/edxml}attachments')

            attachments = OrderedDict()
            for attachment in attachments_element if attachments_element is not None else []:
                attachments[attachment.tag[24:]] = attachment.text if attachment.text is not None else ''

            self._attachments = AttachmentSet(attachments, update_attachment=self.__update_attachment)

            return self._attachments

    def get_foreign_attributes(self):
        """
        Returns any non-edxml event attributes as a dictionary having
        the attribute names as keys and their associated values. The
        namespace is prepended to the keys in James Clark notation:

        {'{http://some/foreign/namespace}attribute': 'value'

        Returns: Dict[str, str]

        """
        return {name: value for name, value in self.attrib.items()
                if name.startswith('{') and not name.startswith('{http://edxml.org/edxml}')}

    def get_explicit_parents(self):
        parent_string = self.attrib.get('parents', '')
        # joining an empty list, e.g. ','.join([]), results in an empty string,
        # but splitting an empty string, e.g. ''.split(','), does not results in
        # an empty list, but [''] instead.
        return [] if parent_string == '' else parent_string.split(',')

    def get_element(self):
        return self

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of strings.

        Args:
          properties: Dict(str, List(str)): Event properties

        Returns:
          EDXMLEvent:

        """
        properties_element = self.find('{http://edxml.org/edxml}properties')
        properties_element.clear()

        self._properties = PropertySet(
                properties, update_property=self.__update_property
            )

        for property_name, values in self._properties.items():
            self.__update_property(property_name, values)

        return self

    def set_attachments(self, attachments):
        """

        Set the event attachments. Attachments are specified
        as a dictionary mapping attachment names to strings.

        Args:
          attachments (Dict[str, str]): Attachment dictionary

        Returns:
          ParsedEvent:
        """
        attachments_element = self.find('{http://edxml.org/edxml}attachments')

        if attachments_element is None:
            attachments_element = etree.SubElement(self, '{http://edxml.org/edxml}attachments')

        attachments_element.clear()

        self._attachments = AttachmentSet(attachments, update_attachment=self.__update_attachment)

        for name, attachment in attachments.items():
            self.__update_attachment(name, attachment)

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
        current = self.get_explicit_parents()
        return self.set_parents(current + parent_hashes)

    def set_parents(self, parent_hashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          ParsedEvent:
        """
        if len(parent_hashes) == 0:
            # An empty value for an XML attribute produces and empty attribute,
            # e.g. parents="", but this is not valid for EDXML. If an element has no
            # parents, delete the attribute instead.
            if 'parents' in self.attrib:
                del self.attrib['parents']
        else:
            self.attrib['parents'] = ','.join(set(parent_hashes))
        return self

    def set_foreign_attributes(self, attribs):
        for key, value in attribs.items():
            self.attrib[key] = value

    def get_type_name(self):
        return self.attrib['event-type']

    def get_source_uri(self):
        return self.attrib['source-uri']

    def set_type(self, event_type_name):
        self.attrib['event-type'] = event_type_name

    def set_source(self, source_uri):
        self.attrib['source-uri'] = source_uri


class EventElement(EDXMLEvent):
    """
    This class extends EDXMLEvent to provide an EDXML event representation
    that wraps an etree Element instance, providing a convenient means to
    generate and manipulate EDXML <event> elements. Using this class is
    preferred over using EDXMLEvent if you intend to feed it to EDXMLWriter.
    """

    def __init__(self, properties, event_type_name=None, source_uri=None, parents=None, attachments=None,
                 foreign_attribs=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple strings. Explicit parent
        hashes must be specified as hex encoded strings.

        Args:
          properties (Dict(str, List[str])): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[optional]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          attachments (Optional[Dict[str, str]]): Event attachments dictionary
          foreign_attribs (Optional[Dict[str, str]]) Foreign attributes dictionary

        Returns:
          EventElement:
        """
        self.__element = etree.Element('event')

        if event_type_name is not None:
            self.__element.set('event-type', event_type_name)
        if source_uri is not None:
            self.__element.set('source-uri', source_uri)

        # We cannot simply set parents to an empty value, because this produces an empty attribute.
        # Instead, if the value is empty, it should be left out altogether.
        if parents:
            self.__element.set('parents', ','.join(parents))

        etree.SubElement(self.__element, 'properties')

        super().__init__(properties, event_type_name, source_uri, parents, attachments, foreign_attribs)

        self._foreign_attribs = foreign_attribs if foreign_attribs is not None else {}

    def __str__(self):
        return etree.tostring(self.__element, encoding='unicode')

    def __delitem__(self, key):
        del self.get_properties()[key]

    def __setitem__(self, key, value):
        object_set = PropertyObjectSet(key, value, update=self.__update_property)
        self.__update_property(key, object_set)
        self.get_properties().replace_object_set(key, object_set)

    def __len__(self):
        return len(self.get_properties())

    def __update_property(self, key, value):
        try:
            props = self.__element.find('properties')
        except AttributeError:
            # This happens while the event is copied. The copy
            # implementation sets dictionary keys while there
            # is no __element attribute yet.
            self.__element = etree.Element('event')
            props = etree.SubElement(self.__element, 'properties')

        for existing_value in props.findall(key):
            props.remove(existing_value)

        if value is None:
            return

        for v in value:
            try:
                etree.SubElement(props, key).text = v
            except (TypeError, ValueError):
                if isinstance(v, str):
                    # Value contains illegal characters.
                    if not getattr(self, '_replace_invalid_characters', False):
                        raise
                    # Replace illegal characters with unicode replacement characters.
                    props[-1].text = re.sub(EVIL_XML_CHARS_REGEXP, chr(0xfffd), v)
                else:
                    props[-1].text = to_edxml_object(key, v)

    def __update_attachment(self, attachment_name, value):
        try:
            attachments_element = self.__element.find('attachments')
        except AttributeError:
            # This happens while the event is copied. The copy
            # implementation sets dictionary keys while there
            # is no __element attribute yet.
            self.__element = etree.Element('event')
            etree.SubElement(self.__element, 'properties')
            attachments_element = etree.SubElement(self.__element, 'attachments')

        if attachments_element is None:
            attachments_element = etree.SubElement(self.__element, 'attachments')

        existing_attachment = attachments_element.find(attachment_name)
        if existing_attachment is not None:
            attachments_element.remove(existing_attachment)

        if value is None:
            return

        try:
            etree.SubElement(attachments_element, attachment_name).text = value
        except (TypeError, ValueError):
            if isinstance(value, str):
                # Value contains illegal characters.
                if not getattr(self, '_replace_invalid_characters', False):
                    raise
                # replace illegal characters with unicode replacement characters.
                attachments_element[-1].text = re.sub(EVIL_XML_CHARS_REGEXP, chr(0xfffd), value)
            else:
                attachments_element[-1].text = value

    def __getitem__(self, key):
        return self.get_properties()[key]

    def __contains__(self, key):
        return key in self.get_properties()

    def __iter__(self):
        for p, v in self.get_properties().items():
            if len(v) > 0:
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
    def create(cls, properties, event_type_name=None, source_uri=None, parents=None, attachments=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Note:
          For a slight performance gain, use the EventElement constructor
          directly to create new events.

        Args:
          properties (Dict[str,Union[str,List[str]]]): Dictionary of properties
          event_type_name (Optional[str]): Name of the event type
          source_uri (Optional[str]): Event source URI
          parents (Optional[List[str]]): List of explicit parent hashes
          attachments (Optional[Dict[str, str]]): Event attachments dictionary

        Returns:
          EventElement:
        """
        return cls(
            properties,
            event_type_name,
            source_uri,
            parents,
            attachments
        )

    @classmethod
    def create_from_event(cls, event):
        """

        Creates and returns a new EventElement instance by reading it from
        another EDXML event.

        Args:
          event (EDXMLEvent): The EDXML event to copy data from

        Returns:
          EventElement:
        """

        return cls(
            event.get_properties(),
            event_type_name=event.get_type_name(),
            source_uri=event.get_source_uri(),
            attachments=event.get_attachments(),
            parents=event.get_explicit_parents()
        ).set_foreign_attributes(event.get_foreign_attributes())\
            .replace_invalid_characters(event._replace_invalid_characters)

    @classmethod
    def create_from_xml(cls, event_element):
        """

        Creates and returns a new EventElement instance by reading it from
        specified lxml Element instance.

        Args:
          event_element (etree.Element): The XML element containing the event

        Returns:
          EventElement:
        """

        new = cls({})
        new.__element = event_element

        return new

    def sort(self):
        """

        Sorts the event properties and attachments on their names. This can be helpful when
        comparing differences between events.

        Returns:
            EDXMLEvent:
        """
        props = self.__element.find('properties')
        if props is not None:
            props[:] = sorted(props, key=lambda element: (element.tag, element.text))
            self._properties = None

        attachments = self.__element.find('attachments')
        if attachments is not None:
            attachments[:] = sorted(attachments, key=lambda element: (element.tag, element.text))
            self._attachments = None

        return self

    def get_properties(self):
        if self._properties is None:
            properties = OrderedDict()
            for element in self.__element.find('properties'):
                tag = element.tag
                if tag not in properties:
                    properties[tag] = set()
                properties[tag].add(element.text)

            self._properties = PropertySet(
                properties, update_property=self.__update_property
            )

        return self._properties

    def get_attachments(self):
        if self._attachments is None:
            attachments_element = self.__element.find('attachments')

            attachments = OrderedDict()
            for attachment in attachments_element if attachments_element is not None else []:
                attachments[attachment.tag] = attachment.text

            self._attachments = AttachmentSet(attachments, update_attachment=self.__update_attachment)

        return self._attachments

    def get_foreign_attributes(self):
        attr = self.__element.attrib.items()
        return {name: value for name, value in attr
                if name.startswith('{') and not name.startswith('{http://edxml.org/edxml}')}

    def get_explicit_parents(self):
        parent_string = self.__element.attrib.get('parents', '')
        # joining an empty list, e.g. ','.join([]), results in an empty string,
        # but splitting an empty string, e.g. ''.split(','), does not results in
        # an empty list, but [''] instead.
        return [] if parent_string == '' else parent_string.split(',')

    def get_type_name(self):
        try:
            return self.__element.attrib['event-type']
        except KeyError:
            return None

    def get_source_uri(self):
        try:
            return self.__element.attrib['source-uri']
        except KeyError:
            return None

    def set_properties(self, properties):
        """

        Replaces the event properties with the properties
        from specified dictionary. The dictionary must
        contain property names as keys. The values must be
        lists of strings.

        Args:
          properties: Dict(str, List(str)): Event properties

        Returns:
          EventElement:

        """
        properties_element = self.__element.find('properties')
        properties_element.clear()

        self._properties = PropertySet(
                properties, update_property=self.__update_property
            )

        for property_name, values in self._properties.items():
            self.__update_property(property_name, values)

        return self

    def set_attachments(self, attachments):
        """

        Set the event attachments. Attachments are specified
        as a dictionary mapping attachment names to strings.

        Args:
          attachments (Dict[str, str]): Attachment dictionary

        Returns:
          EventElement:
        """
        attachments_element = self.__element.find('attachments')

        if attachments_element is None:
            attachments_element = etree.SubElement(self.__element, 'attachments')

        attachments_element.clear()

        self._attachments = AttachmentSet(attachments, update_attachment=self.__update_attachment)

        for name, attachment in attachments.items():
            self.__update_attachment(name, attachment)

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
        current = self.get_explicit_parents()
        return self.set_parents(current + parent_hashes)

    def set_parents(self, parent_hashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          parent_hashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          EventElement:
        """
        if len(parent_hashes) == 0:
            # An empty value for an XML attribute produces and empty attribute,
            # e.g. parents="", but this is not valid for EDXML. If an element has no
            # parents, delete the attribute instead.
            if 'parents' in self.__element.attrib:
                del self.__element.attrib['parents']
        else:
            self.__element.attrib['parents'] = ','.join(set(parent_hashes))
        return self

    def set_foreign_attributes(self, attribs):
        for key, value in attribs.items():
            self.__element.attrib[key] = value
        return self

    def set_type(self, event_type_name):
        self.__element.attrib['event-type'] = event_type_name

    def set_source(self, source_uri):
        self.__element.attrib['source-uri'] = source_uri
