# -*- coding: utf-8 -*-

import re
import hashlib


from collections import MutableMapping
from collections import defaultdict
from lxml import etree
from copy import deepcopy
from decimal import Decimal
from edxml.EDXMLBase import EvilCharacterFilter


class EDXMLEvent(MutableMapping):
    """Class representing an EDXML event.

    The event allows its properties to be accessed
    and set much like a dictionary:

        Event['property-name'] = 'value'

    Note:
      Properties are lists of object values. On assignment,
      non-list values are automatically wrapped into lists.

    """

    def __init__(self, Properties, EventTypeName=None, SourceUri=None, Parents=None, Content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Args:
          Properties (Dict[str,List[unicode]]): Dictionary of properties
          EventTypeName (Optional[str]): Name of the event type
          SourceUri (Optional[str]): Event source URI
          Parents (Optional[List[str]]): List of explicit parent hashes
          Content (Optional[unicode]): Event content

        Returns:
          EDXMLEvent
        """
        self.Properties = Properties
        self.EventTypeName = EventTypeName
        self.SourceUri = SourceUri
        self.Parents = set(Parents) if Parents is not None else set()
        self.Content = unicode(Content) if Content else u''

    def __str__(self):
        return "\n".join(
            ['%20s:%s' % (Property, ','.join([unicode(Value) for Value in Values]))
             for Property, Values in self.Properties.iteritems()]
        )

    def __delitem__(self, key):
        self.Properties.pop(key, None)

    def __setitem__(self, key, value):
        if type(value) == list:
            self.Properties[key] = value
        else:
            self.Properties[key] = [value]

    def __len__(self):
        return len(self.Properties)

    def __getitem__(self, key):
        try:
            return self.Properties[key]
        except KeyError:
            return []

    def __contains__(self, key):
        try:
            self.Properties[key][0]
        except (KeyError, IndexError):
            return False
        else:
            return True

    def __iter__(self):
        for PropertyName, Objects in self.Properties.items():
            yield PropertyName

    def getAny(self, propertyName, default=None):
        """

        Convenience method for fetching any of possibly multiple
        object values of a specific event property. If the requested
        property has no object values, the specified default value
        is returned in stead.

        Args:
          propertyName (string): Name of requested property
          default: Default return value

        Returns:

        """
        value = self.get(propertyName)
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
        return EDXMLEvent(self.Properties.copy(), self.EventTypeName, self.SourceUri, list(self.Parents), self.Content)

    @classmethod
    def Create(cls, Properties, EventTypeName=None, SourceUri=None, Parents=None, Content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Note:
          For a slight performance gain, use the EDXMLEvent constructor
          directly to create new events.

        Args:
          Properties (Dict[str,Union[unicode,List[unicode]]]): Dictionary of properties
          EventTypeName (Optional[str]): Name of the event type
          SourceUri (Optional[str]): Event source URI
          Parents (Optional[List[str]]): List of explicit parent hashes
          Content (Optional[unicode]): Event content

        Returns:
          EDXMLEvent:
        """
        return cls(
            {Property: Value if type(Value) == list else [
                Value] for Property, Value in Properties.items()},
            EventTypeName,
            SourceUri,
            Parents,
            Content
        )

    def GetTypeName(self):
        """

        Returns the name of the event type.

        Returns:
          str: The event type name

        """
        return self.EventTypeName

    def GetSourceUri(self):
        """

        Returns the URI of the event source.

        Returns:
          str: The source URI

        """
        return self.SourceUri

    def GetProperties(self):
        """

        Returns a dictionary containing property names
        as keys. The values are lists of object values.

        Returns:
          Dict[str, List[unicode]]: Event properties

        """
        return self.Properties

    def GetExplicitParents(self):
        """

        Returns a list of sticky hashes of parent
        events. The hashes are hex encoded strings.

        Returns:
          List[str]: List of parent hashes

        """
        return list(self.Parents)

    def GetContent(self):
        """

        Returns the content of the event.

        Returns:
          unicode: Event content

        """
        return self.Content

    @classmethod
    def Read(cls, EventTypeName, SourceUri, EventElement):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          EventTypeName (str): The name of the event type
          SourceUri (str): The URI of the EDXML event source
          EventElement (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        Content = ''
        PropertyObjects = {}
        for element in EventElement:
            if element.tag == 'properties':
                for propertyElement in element:
                    PropertyName = propertyElement.tag
                    if PropertyName not in PropertyObjects:
                        PropertyObjects[PropertyName] = []
                    PropertyObjects[PropertyName].append(propertyElement.text)
            elif element.tag == 'content':
                Content = element.text

        return cls(PropertyObjects, EventTypeName, SourceUri, EventElement.attrib.get('parents'), Content)

    def SetProperties(self, properties):
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
        self.Properties = properties
        return self

    def CopyPropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EDXMLEvent):
         PropertyMap (dict(str,str)):

        Returns:
          EDXMLEvent:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                SourceProperties = SourceEvent.Properties[Source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(SourceProperties) > 0:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self.Properties:
                        self.Properties[Target] = []
                        self.Properties[Target].extend(SourceProperties)

        return self

    def MovePropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EDXMLEvent):
         PropertyMap (dict(str,str)):

        Returns:
          EDXMLEvent:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self.Properties:
                        self.Properties[Target] = []
                    self.Properties[Target].extend(
                        SourceEvent.Properties[Source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del SourceEvent.Properties[Source]

        return self

    def SetType(self, EventTypeName):
        """

        Set the event type.

        Args:
          EventTypeName (str): Name of the event type

        Returns:
          EDXMLEvent:
        """
        self.EventTypeName = EventTypeName
        return self

    def SetContent(self, Content):
        """

        Set the event content.

        Args:
          Content (unicode): Content string

        Returns:
          EDXMLEvent:
        """
        self.Content = Content
        return self

    def SetSource(self, SourceUri):
        """

        Set the event source.

        Args:
          SourceUri (str): EDXML source URI

        Returns:
          EDXMLEvent:
        """
        self.SourceUri = SourceUri
        return self

    def AddParents(self, ParentHashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          ParentHashes (List[str]): list of sticky hash, as hexadecimal strings

        Returns:
          EDXMLEvent:
        """
        self.Parents.update(ParentHashes)
        return self

    def SetParents(self, ParentHashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          ParentHashes (List[str]): list of sticky hash, as hexadecimal strings

        Returns:
          EDXMLEvent:
        """
        self.Parents = set(ParentHashes)
        return self

    def MergeWith(self, collidingEvents, edxmlOntology):
        """
        Merges the event with event data from a number of colliding
        events. It returns True when the event was updated
        as a result of the merge, returns False otherwise.

        Args:
          collidingEvents (List[EDXMLEvent]): Iterable yielding events
          edxmlOntology (edxml.ontology.Ontology): The EDXML ontology

        Returns:
          bool: Event was changed or not

        """

        eventType = edxmlOntology.GetEventType(self.EventTypeName)
        properties = eventType.GetProperties()
        propertyNames = properties.keys()
        uniqueProperties = eventType.GetUniqueProperties()

        if len(uniqueProperties) == 0:
            raise TypeError(
                "MergeEvent was called for event type %s, which is not a unique event type." % self.EventTypeName)

        EventObjectsA = self.GetProperties()

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

        Original = {}
        Source = {}
        Target = {}

        for PropertyName in propertyNames:
            if PropertyName in EventObjectsA:
                Original[PropertyName] = set(EventObjectsA[PropertyName])
                Target[PropertyName] = set(EventObjectsA[PropertyName])
            else:
                Original[PropertyName] = set()
                Target[PropertyName] = set()
            Source[PropertyName] = set()

        for event in collidingEvents:
            EventObjectsB = event.GetProperties()
            for PropertyName in propertyNames:
                if PropertyName in EventObjectsB:
                    Source[PropertyName].update(EventObjectsB[PropertyName])

        # Now we update the objects in Target
        # using the values in Source
        for PropertyName in Source:

            if PropertyName in uniqueProperties:
                # Unique property, does not need to be merged.
                continue

            MergeStrategy = properties[PropertyName].GetMergeStrategy()

            if MergeStrategy in ('min', 'max'):
                # We have a merge strategy that requires us to cast
                # the object values into numbers.
                SplitDataType = properties[PropertyName].GetDataType(
                ).GetSplit()
                if SplitDataType[0] in ('number', 'datetime'):
                    if MergeStrategy in ('min', 'max'):
                        Values = set()
                        if SplitDataType[0] == 'datetime':
                            # Note that we add the datetime values as
                            # regular strings and just let min() and max()
                            # use lexicographical sorting to determine which
                            # of the datetime values to pick.
                            Values.update(Source[PropertyName])
                            Values.update(Target[PropertyName])
                        else:
                            if SplitDataType[1] in ('float', 'double'):
                                Values.update(float(Value)
                                              for Value in Source[PropertyName])
                                Values.update(float(Value)
                                              for Value in Target[PropertyName])
                            elif SplitDataType[1] == 'decimal':
                                Values.update(Decimal(Value)
                                              for Value in Source[PropertyName])
                                Values.update(Decimal(Value)
                                              for Value in Target[PropertyName])
                            else:
                                Values.update(int(Value)
                                              for Value in Source[PropertyName])
                                Values.update(int(Value)
                                              for Value in Target[PropertyName])

                        if MergeStrategy == 'min':
                            Target[PropertyName] = {str(min(Values))}
                        else:
                            Target[PropertyName] = {str(max(Values))}

                        if SplitDataType[1] in ('float', 'double'):
                            Target[PropertyName] = {
                                str(float(next(iter(Target[PropertyName]))) + len(collidingEvents))}
                        elif SplitDataType[1] == 'decimal':
                            Target[PropertyName] = {
                                str(Decimal(next(iter(Target[PropertyName]))) + len(collidingEvents))}
                        else:
                            Target[PropertyName] = {
                                str(int(next(iter(Target[PropertyName]))) + len(collidingEvents))}

            elif MergeStrategy == 'add':
                Target[PropertyName].update(Source[PropertyName])

            elif MergeStrategy == 'replace':
                Target[PropertyName] = set(
                    collidingEvents[-1].get(PropertyName, []))

        SourceParents = set(
            parent for sourceEvent in collidingEvents for parent in sourceEvent.GetExplicitParents())

        # Merge the explicit event parents
        if len(SourceParents) > 0:
            OriginalParents = self.GetExplicitParents()
            self.SetParents(self.GetExplicitParents() + list(SourceParents))
        else:
            OriginalParents = set()

        # Determine if anything changed
        EventUpdated = False
        for PropertyName in propertyNames:
            if PropertyName not in Original and len(Target[PropertyName]) > 0:
                EventUpdated = True
                break
            if Target[PropertyName] != Original[PropertyName]:
                EventUpdated = True
                break

        if not EventUpdated:
            if len(SourceParents) > 0:
                if OriginalParents != SourceParents:
                    EventUpdated = True

        # Modify event if needed
        if EventUpdated:
            self.SetProperties(Target)
            return True
        else:
            return False

    def ComputeStickyHash(self, edxmlOntology, encoding='hex'):
        """

        Computes the sticky hash of the event. By default, the hash
        will be encoded into a hexadecimal string. The encoding can
        be adjusted by setting the encoding argument to any string
        encoding that is supported by the str.encode() method.

        Args:
          edxmlOntology (edxml.ontology.Ontology): An EDXML ontology
          encoding (str): Desired output encoding

        Note:
          The object values of the event must be valid EDXML object value strings or
          values that can be cast to valid EDXML object value strings.

        Returns:
          str: String representation of the hash.

        """

        eventType = edxmlOntology.GetEventType(self.EventTypeName)
        objects = self.GetProperties()
        hashProperties = eventType.GetHashProperties()

        objectStrings = set('%s:%s' % (p, v)
                            for p in objects if p in hashProperties for v in objects[p])

        # Now we compute the SHA1 hash value of the byte
        # string representation of the event, and output in hex

        if eventType.IsUnique():
            return hashlib.sha1(
                '%s\n%s\n%s' % (self.SourceUri, self.EventTypeName,
                                '\n'.join(sorted(objectStrings)))
            ).digest().encode(encoding)
        else:
            return hashlib.sha1(
                '%s\n%s\n%s\n%s' % (self.SourceUri, self.EventTypeName, '\n'.join(
                    sorted(objectStrings)), self.Content)
            ).digest().encode(encoding)


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
            del self.__properties
        except AttributeError:
            pass

    def __setitem__(self, key, value):
        if type(value) == list:
            props = self.find('properties')
            for existingValue in props.findall(key):
                props.remove(existingValue)
            for v in value:
                try:
                    etree.SubElement(props, key).text = v
                except (TypeError, ValueError):
                    if type(v) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        props[-1].text = unicode(
                            re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), v))
                    else:
                        raise ValueError(
                            'Value of property %s is not a string: %s' % (key, repr(value)))
        else:
            props = self.find('properties')
            for existingValue in props.findall(key):
                props.remove(existingValue)
            try:
                etree.SubElement(props, key).text = value
            except (TypeError, ValueError):
                if type(value) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    props[-1].text = unicode(
                        re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), value))
                else:
                    raise ValueError(
                        'Value of property %s is not a string: %s' % (key, repr(value)))
        try:
            del self.__properties
        except AttributeError:
            pass

    def __len__(self):
        try:
            return len(self.__properties)
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.find('properties'):
                self.__properties[element.tag].append(element.text)
            return len(self.__properties)

    def __getitem__(self, key):
        try:
            return self.__properties[key]
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.find('properties'):
                self.__properties[element.tag].append(element.text)
            return self.__properties[key]

    def __contains__(self, key):
        try:
            return key in self.__properties
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.find('properties'):
                self.__properties[element.tag].append(element.text)
            return key in self.__properties

    def __iter__(self):
        try:
            for p in self.__properties.keys():
                yield p
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.find('properties'):
                self.__properties[element.tag].append(element.text)
            for p in self.__properties.keys():
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
            del self.__properties
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
    def Create(cls, Properties, EventTypeName=None, SourceUri=None, Parents=None, Content=None):
        """

        This override of the Create() method of the EDXMLEvent class
        only raises exceptions, because ParsedEvent objects can only
        be created by parsers.

        Raises:
          NotImplementedError

        """
        raise NotImplementedError(
            'ParsedEvent objects can only be created by parsers')

    @classmethod
    def Read(cls, EventTypeName, SourceUri, EventElement):
        """

        Creates and returns a new EDXMLEvent instance by reading it from
        specified lxml Element instance.

        Args:
          EventTypeName (str): The name of the event type
          SourceUri (str): The URI of the EDXML event source
          EventElement (etree.Element): The XML element containing the event

        Returns:
          EDXMLEvent:
        """
        Content = ''
        PropertyObjects = {}
        for element in EventElement:
            if element.tag == 'properties':
                for propertyElement in element:
                    PropertyName = propertyElement.tag
                    if PropertyName not in PropertyObjects:
                        PropertyObjects[PropertyName] = []
                    PropertyObjects[PropertyName].append(propertyElement.text)
            elif element.tag == 'content':
                Content = element.text

        return cls(PropertyObjects, EventTypeName, SourceUri, EventElement.attrib.get('parents'), Content)

    def GetProperties(self):
        try:
            return self.__properties
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.find('properties'):
                self.__properties[element.tag].append(element.text)
            return self.__properties

    def GetContent(self):
        try:
            return self.find('content').text
        except AttributeError:
            return ''

    def GetExplicitParents(self):
        try:
            return self.attrib['parents'].split(',')
        except KeyError:
            return []

    def SetProperties(self, properties):
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
        propertiesElement = self.find('properties')
        propertiesElement.clear()

        for propertyName, values in properties.items():
            for value in values:
                etree.SubElement(propertiesElement, propertyName).text = value

        try:
            del self.__properties
        except AttributeError:
            pass

        return self

    def CopyPropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EDXMLEvent): Source event
         PropertyMap (Dict[str,str]): Property mapping

        Returns:
          EDXMLEvent:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                SourceProperties = SourceEvent.Properties[Source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(SourceProperties) > 0:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self:
                        self[Target] = []
                    self[Target].extend(SourceProperties)

        return self

    def MovePropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EDXMLEvent): Source event
         PropertyMap (Dict[str,str]): Property mapping

        Returns:
          EDXMLEvent:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self.Properties:
                        self[Target] = []
                    self[Target].extend(SourceEvent.Properties[Source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del SourceEvent[Source]

        return self

    def SetContent(self, Content):
        """

        Set the event content.

        Args:
          Content (unicode): Content string

        Returns:
          ParsedEvent:
        """
        try:
            self.find('content').text = Content
        except (TypeError, ValueError):
            if type(Content) in (str, unicode):
                # Value contains illegal characters,
                # replace them with unicode replacement characters.
                self.find('content').text = unicode(
                    re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), Content))
            else:
                raise ValueError(
                    'Event content value is not a string: %s' % repr(Content))
        return self

    def AddParents(self, ParentHashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          ParentHashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          ParsedEvent:
        """
        self.attrib.set('parents', ','.join(self.attrib.get(
            'parents').split(',').append(ParentHashes)))
        return self

    def SetParents(self, ParentHashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          ParentHashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          ParsedEvent:
        """
        self.attrib.set('parents', ','.join(ParentHashes))
        return self


class EventElement(EDXMLEvent, EvilCharacterFilter):
    """
    This class extends EDXMLEvent to provide an EDXML event representation
    that wraps an etree Element instance, providing a convenient means to
    generate and manipulate EDXML <event> elements. Using this class is
    preferred over using EDXMLEvent if you intend to feed it to EDXMLWriter
    or SimpleEDXMLWriter.
    """

    def __init__(self, Properties, EventTypeName=None, SourceUri=None, Parents=None, Content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        must be lists of one or multiple unicode strings. Explicit parent
        hashes must be specified as hex encoded strings.

        Args:
          Properties (Dict(str, List[unicode])): Dictionary of properties
          EventTypeName (Optional[str]): Name of the event type
          SourceUri (Optional[optional]): Event source URI
          Parents (Optional[List[str]]): List of explicit parent hashes
          Content (Optional[unicode]): Event content

        Returns:
          EventElement:
        """
        super(EventElement, self).__init__(Properties,
                                           EventTypeName, SourceUri, Parents, Content)

        # These are now kept in an etree element.
        self.Properties = None
        self.Parents = None
        self.Content = None

        new = etree.Element('event')
        if Parents:
            new.set('parents', ','.join(Parents))

        p = etree.SubElement(new, 'properties')
        for propertyName, values in Properties.iteritems():
            for value in values:
                try:
                    etree.SubElement(p, propertyName).text = value
                except (TypeError, ValueError):
                    if type(value) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        charFilter = EvilCharacterFilter()
                        p[-1].text = unicode(
                            re.sub(charFilter.evilXmlCharsRegExp, unichr(0xfffd), value))
                    else:
                        raise ValueError(
                            'Object value is not a string: ' + repr(value))
        if Content:
            try:
                etree.SubElement(new, 'content').text = Content
            except (TypeError, ValueError):
                if type(Content) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    charFilter = EvilCharacterFilter()
                    new[-1].text = unicode(
                        re.sub(charFilter.evilXmlCharsRegExp, unichr(0xfffd), Content))
                else:
                    raise ValueError(
                        'Event content is not a string: ' + repr(Content))

        self.element = new
        self.__properties = None

    def __str__(self):
        return etree.tostring(self.element)

    def __delitem__(self, key):
        props = self.element.find('properties')
        for element in props.findall(key):
            props.remove(element)
        self.__properties = None

    def __setitem__(self, key, value):
        if type(value) == list:
            props = self.element.find('properties')
            for existingValue in props.findall(key):
                props.remove(existingValue)
            for v in set(value):
                try:
                    etree.SubElement(props, key).text = v
                except (TypeError, ValueError):
                    if type(v) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        props[-1].text = unicode(
                            re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), v))
                    else:
                        raise ValueError(
                            'Value of property %s is not a string: %s' % (key, repr(value)))
        else:
            props = self.element.find('properties')
            for existingValue in props.findall(key):
                props.remove(existingValue)
            try:
                etree.SubElement(props, key).text = value
            except (TypeError, ValueError):
                if type(value) in (str, unicode):
                    # Value contains illegal characters,
                    # replace them with unicode replacement characters.
                    props[-1].text = unicode(
                        re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), value))
                else:
                    raise ValueError(
                        'Value of property %s is not a string: %s' % (key, repr(value)))
        self.__properties = None

    def __len__(self):
        try:
            return len(self.__properties)
        except TypeError:
            self.__properties = defaultdict(list)
            for element in self.element.find('properties'):
                self.__properties[element.tag].append(element.text)
            return len(self.__properties)

    def __getitem__(self, key):
        try:
            return self.__properties[key]
        except TypeError:
            self.__properties = defaultdict(list)
            for element in self.element.find('properties'):
                self.__properties[element.tag].append(element.text)
            return self.__properties[key]

    def __contains__(self, key):
        try:
            return key in self.__properties
        except TypeError:
            self.__properties = defaultdict(list)
            for element in self.element.find('properties'):
                self.__properties[element.tag].append(element.text)
            return key in self.__properties

    def __iter__(self):
        try:
            for p in self.__properties.keys():
                yield p
        except AttributeError:
            self.__properties = defaultdict(list)
            for element in self.element.find('properties'):
                self.__properties[element.tag].append(element.text)
            for p in self.__properties.keys():
                yield p

    def copy(self):
        """

        Returns a copy of the event.

        Returns:
           EventElement:
        """
        return deepcopy(self)

    @classmethod
    def Create(cls, Properties, EventTypeName=None, SourceUri=None, Parents=None, Content=None):
        """

        Creates a new EDXML event. The Properties argument must be a
        dictionary mapping property names to object values. Object values
        may be single values or a list of multiple object values. Explicit parent
        hashes must be specified as hex encoded strings.

        Note:
          For a slight performance gain, use the EventElement constructor
          directly to create new events.

        Args:
          Properties (Dict[str,Union[unicode,List[unicode]]]): Dictionary of properties
          EventTypeName (Optional[str]): Name of the event type
          SourceUri (Optional[str]): Event source URI
          Parents (Optional[List[str]]): List of explicit parent hashes
          Content (Optional[unicode]): Event content

        Returns:
          EventElement:
        """
        return cls(
            {Property: Value if type(Value) == list else [
                Value] for Property, Value in Properties.items()},
            EventTypeName,
            SourceUri,
            Parents,
            Content
        )

    @classmethod
    def Read(cls, EventTypeName, SourceUri, EventElement):
        """

        Creates and returns a new EventElement instance by reading it from
        specified lxml Element instance.

        Args:
          EventTypeName (str): The name of the event type
          SourceUri (str): The URI of the EDXML event source
          EventElement (etree.Element): The XML element containing the event

        Returns:
          EventElement:
        """

        new = cls({})
        new.element = EventElement

        return new

    def GetProperties(self):
        try:
            return dict(self.__properties)
        except TypeError:
            self.__properties = defaultdict(list)
            for element in self.element.find('properties'):
                self.__properties[element.tag].append(element.text)
            return self.__properties

    def GetContent(self):
        try:
            return self.element.find('content').text
        except AttributeError:
            # No content.
            return ''

    def GetExplicitParents(self):
        try:
            return self.element.attrib['parents'].split(',')
        except KeyError:
            return []

    def SetProperties(self, properties):
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
        propertiesElement = self.element.find('properties')
        propertiesElement.clear()

        for propertyName, values in properties.items():
            for value in values:
                try:
                    etree.SubElement(propertiesElement,
                                     propertyName).text = value
                except (TypeError, ValueError):
                    if type(value) in (str, unicode):
                        # Value contains illegal characters,
                        # replace them with unicode replacement characters.
                        propertiesElement[-1].text = unicode(
                            re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), value))
                    else:
                        raise ValueError('Value of property %s is not a string: %s' % (
                            propertyName, repr(value)))

        self.__properties = None

        return self

    def CopyPropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EventElement): Source event
         PropertyMap (Dict[str,str]): Property mapping

        Returns:
          EventElement:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                SourceProperties = SourceEvent.Properties[Source]
            except KeyError:
                # Source property does not exist.
                continue
            if len(SourceProperties) > 0:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self:
                        self[Target] = []
                    self[Target].extend(SourceProperties)

        return self

    def MovePropertiesFrom(self, SourceEvent, PropertyMap):
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
         SourceEvent (EventElement): Source event
         PropertyMap (Dict[str,str]): Property mapping

        Returns:
          EventElement:
        """

        for Source, Targets in PropertyMap.iteritems():
            try:
                for Target in (Targets if isinstance(Targets, list) else [Targets]):
                    if Target not in self.Properties:
                        self[Target] = []
                    self[Target].extend(SourceEvent.Properties[Source])
            except KeyError:
                # Source property does not exist.
                pass
            else:
                del SourceEvent[Source]

        return self

    def SetContent(self, Content):
        """

        Set the event content.

        Args:
          Content (unicode): Content string

        Returns:
          EventElement:
        """
        try:
            self.element.find('content').text = Content
        except AttributeError:
            etree.SubElement(self.element, 'content').text = Content
        except (TypeError, ValueError):
            if type(Content) in (str, unicode):
                # Value contains illegal characters,
                # replace them with unicode replacement characters.
                self.element.find('content').text = unicode(
                    re.sub(self.evilXmlCharsRegExp, unichr(0xfffd), Content))
            else:
                raise ValueError(
                    'Event content value is not a string: %s' % repr(Content))
        return self

    def AddParents(self, ParentHashes):
        """

        Add the specified sticky hashes to the list
        of explicit event parents.

        Args:
          ParentHashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          EventElement:
        """
        self.element.attrib.set('parents', ','.join(
            self.element.attrib.get('parents').split(',').append(ParentHashes)))
        return self

    def SetParents(self, ParentHashes):
        """

        Replace the set of explicit event parents with the specified
        list of sticky hashes.

        Args:
          ParentHashes (List[str]): list of sticky hashes, as hexadecimal strings

        Returns:
          EventElement:
        """
        self.element.attrib.set('parents', ','.join(ParentHashes))
        return self
