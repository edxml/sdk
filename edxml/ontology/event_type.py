# -*- coding: utf-8 -*-
from typing import Dict

import edxml
import re

from io import BytesIO
from collections import MutableMapping
from dateutil.parser import parse
from dateutil import relativedelta
from iso3166 import countries
from lxml import etree
from lxml.builder import ElementMaker
from termcolor import colored

from edxml.error import EDXMLValidationError
from edxml.ontology import OntologyElement, normalize_xml_token


class EventType(OntologyElement, MutableMapping):
    """
    Class representing an EDXML event type. The class provides
    access to event properties by means of a dictionary interface.
    For each of the properties there is a key matching the name of
    the event property, the value is the property itself.
    """

    NAME_PATTERN = re.compile("^[a-z0-9.-]*$")
    CLASS_LIST_PATTERN = re.compile("^[a-z0-9, ]*$")
    TEMPLATE_PATTERN = re.compile('\\[\\[([^\\]]*)\\]\\]')
    KNOWN_FORMATTERS = (
        'TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
        'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'COUNTRYCODE', 'MERGE',
        'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY', 'NEWPAR', 'URL', 'UPPERCASE'
    )

    def __init__(self, ontology, name, display_name_singular=None, display_name_plural=None, description=None,
                 class_list='', summary='no description available', story='no description available', parent=None):

        display_name_singular = display_name_singular or name.replace('.', ' ')
        display_name_plural = display_name_plural or display_name_singular + 's'

        self.__attr = {
            'name': name,
            'display-name-singular': display_name_singular,
            'display-name-plural': display_name_plural,
            'description': description or name,
            'classlist': class_list,
            'summary': summary,
            'story': story.replace('\n', '[[NEWPAR:]]'),
            'timespan-start': None,
            'timespan-end': None,
            'version': 1
        }

        self.__properties = {}      # type: Dict[str, edxml.ontology.EventProperty]
        self.__relations = {}       # type: Dict[str,edxml.ontology.PropertyRelation]
        self.__parent = parent      # type: edxml.ontology.EventTypeParent
        self.__attachments = {}     # type: Dict[str, edxml.ontology.EventTypeAttachment]
        self.__relax_ng = None      # type: etree.RelaxNG
        self.__ontology = ontology  # type: edxml.ontology.Ontology

        self.__parent_description = None  # type: str

        # type: Dict[str, edxml.ontology.EventProperty]
        self.__cachedUniqueProperties = None
        # type: Dict[str, edxml.ontology.EventProperty]
        self.__cached_is_timeless = None
        self.__cachedHashProperties = None

    def __delitem__(self, property_name):
        if property_name in self.__properties:
            del self.__properties[property_name]
            self._child_modified_callback()

    def __setitem__(self, property_name, property_instance):
        if isinstance(property_instance, edxml.ontology.EventProperty):
            self.__properties[property_name] = property_instance
            self._child_modified_callback()
        else:
            raise TypeError('Not an event property: %s' %
                            repr(property_instance))

    def __len__(self):
        return len(self.__properties)

    def __getitem__(self, property_name):
        """

        Args:
          property_name (str): Name of an event property

        Returns:
          edxml.ontology.EventProperty:
        """
        try:
            return self.__properties[property_name]
        except KeyError:
            raise Exception('Event type %s has no property named %s.' %
                            (self.__attr['name'], property_name))

    def __contains__(self, property_name):
        try:
            self.__properties[property_name]
        except (KeyError, IndexError):
            return False
        else:
            return True

    def __iter__(self):
        """

        Yields:
          Dict[str, edxml.ontology.EventProperty]
        """
        for propertyName, prop in self.__properties.items():
            yield propertyName

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__cachedUniqueProperties = None
        self.__cached_is_timeless = None
        self.__cachedHashProperties = None
        self.__ontology._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def get_name(self):
        """

        Returns the event type name

        Returns:
          str:
        """
        return self.__attr['name']

    def get_description(self):
        """

        Returns the event type description

        Returns:
          str:
        """
        return self.__attr['description']

    def get_display_name_singular(self):
        """

        Returns the event type display name, in singular form.

        Returns:
          str:
        """
        return self.__attr['display-name-singular']

    def get_display_name_plural(self):
        """

        Returns the event type display name, in plural form.

        Returns:
          Optional[str]:
        """
        return self.__attr['display-name-plural']

    def get_timespan_property_name_start(self):
        """

        Returns the name of the property that defines the start
        of the time span of the events. Returns None when the start
        of the event time span is the smallest of the event timestamps.

        Returns:
            Optional[str]:
        """
        return self.__attr['timespan-start']

    def get_timespan_property_name_end(self):
        """

        Returns the name of the property that defines the end
        of the time span of the events. Returns None when the end
        of the event time span is the largest of the event timestamps.

        Returns:
            str:
        """
        return self.__attr['timespan-end']

    def get_classes(self):
        """

        Returns the list of classes that this event type
        belongs to.

        Returns:
          List[str]:
        """
        return self.__attr['classlist'].split(',')

    def get_properties(self):
        """

        Returns a dictionary containing all properties
        of the event type. The keys in the dictionary
        are the property names, the values are the
        EDXMLProperty instances.

        Returns:
           Dict[str,edxml.ontology.EventProperty]: Properties
        """
        return self.__properties

    def get_unique_properties(self):
        """

        Returns a dictionary containing all unique properties
        of the event type. The keys in the dictionary
        are the property names, the values are the
        EDXMLProperty instances.

        Returns:
           Dict[str, edxml.ontology.EventProperty]: Properties
        """
        return {n: p for n, p in self.__properties.items() if p.is_unique()}

    def get_hash_properties(self):
        """

        Returns a dictionary containing all properties
        of the event type that must be included when
        computing its sticky hash. The keys in the dictionary
        are the property names, the values are the
        EDXMLProperty instances.

        Returns:
           Dict[str, edxml.ontology.EventProperty]: Properties
        """

        if self.__cachedHashProperties is None:
            props = {}

            for n, p in self.__properties.items():
                data_type = p.get_data_type().get_split()

                if not self.is_unique() or p.is_unique():
                    if data_type[0] != 'number' or data_type[1] not in ('float', 'double'):
                        # Floating point objects are ignored.
                        props[n] = p

            self.__cachedHashProperties = props

        return self.__cachedHashProperties

    def get_property_relations(self):
        """

        Returns a dictionary containing the property relations that
        are defined in the event type. The keys are relation IDs that
        should be considered opaque.

        Returns:
          Dict[str,edxml.ontology.PropertyRelation]:
        """
        return self.__relations

    def get_attachment(self, name):
        """

        Returns the specified attachment definition.

        Raises:
            KeyError

        Returns:
          edxml.ontology.EventTypeAttachment:
        """
        return self.__attachments[name]

    def get_attachments(self):
        """

        Returns a dictionary containing the attachments that
        are defined for the event type. The keys are attachment IDs.

        Returns:
          Dict[str,edxml.ontology.EventTypeAttachment]:
        """
        return self.__attachments

    def has_class(self, class_name):
        """

        Returns True if specified class is in the list of
        classes that this event type belongs to, return False
        otherwise.

        Args:
          class_name (str): The class name

        Returns:
          bool:
        """
        return class_name in self.__attr['classlist'].split(',')

    def is_unique(self):
        """

        Returns True if the event type is a unique
        event type, returns False otherwise.

        Returns:
          bool:
        """
        if self.__cachedUniqueProperties is None:
            self.__cachedUniqueProperties = {}
            for propertyName, eventProperty in self.__properties.items():
                if eventProperty.is_unique():
                    self.__cachedUniqueProperties[propertyName] = eventProperty

        return len(self.__cachedUniqueProperties) > 0

    def get_timespan_property_names(self):
        """
        Returns a tuple containing the names of the properties that
        determine the start and end of the event time spans, in that order.
        Note that either may be None.

        Returns:
            Tuple[Optional[str], Optional[str]]

        """
        return self.__attr['timespan-start'], self.__attr['timespan-end']

    def is_timeless(self):
        """

        Returns True when the event type is timeless, which
        means that it has no properties that are associated with
        the datetime data type. Returns False otherwise.

        Returns:
            bool:
        """
        if self.__cached_is_timeless is None:
            self.__cached_is_timeless = True
            for propertyName, eventProperty in self.__properties.items():
                if eventProperty.get_data_type().is_datetime():
                    self.__cached_is_timeless = False

        return self.__cached_is_timeless

    def is_timeful(self):
        """

        Returns True when the event type is timeful, which
        means that it has at least one property that is
        associated with the datetime data type. Returns
        False otherwise.

        Returns:
            bool:
        """
        return not self.is_timeless()

    def get_summary_template(self):
        """

        Returns the event summary template.

        Returns:
          str:
        """
        return self.__attr['summary']

    def get_story_template(self):
        """

        Returns the event story template.

        Returns:
          str:
        """
        return self.__attr['story']

    def get_parent(self):
        """

        Returns the parent event type, or None
        if no parent has been defined.

        Returns:
          EventTypeParent: The parent event type
        """
        return self.__parent

    def get_version(self):
        """

        Returns the version of the source definition.

        Returns:
          int:
        """

        return self.__attr['version']

    def create_property(self, name, object_type_name, description=None):
        """

        Create a new event property.

        Note:
           The description should be really short, indicating
           which role the object has in the event type.

        Args:
          name (str): Property name
          object_type_name (str): Name of the object type
          description (str): Property description

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        if name not in self.__properties:
            object_type = self.__ontology.get_object_type(object_type_name)
            if not object_type:
                # Object type is not defined, try to load it from
                # any registered ontology bricks
                self.__ontology._import_object_type_from_brick(object_type_name)
                object_type = self.__ontology.get_object_type(object_type_name)
            if object_type:
                self.__properties[name] = edxml.ontology.EventProperty(self, name, object_type, description).validate()
            else:
                raise Exception(
                    'Attempt to create property "%s" of event type "%s" referring to undefined object type "%s".' %
                    (name, self.get_name(), object_type_name)
                )
        else:
            raise Exception(
                'Attempt to create existing property "%s" of event type "%s".' %
                (name, self.get_name())
            )

        self._child_modified_callback()
        return self.__properties[name]

    def add_property(self, prop):
        """

        Add specified property

        Args:
          prop (edxml.ontology.EventProperty): EventProperty instance

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__properties[prop.get_name()] = prop.validate()
        self._child_modified_callback()
        return self

    def remove_property(self, property_name):
        """

        Removes specified property from the event type.

        Notes:
          Since the EventType class has a dictionary interface
          for accessing event type properties, you can also use
          the del operator to delete a property.

        Args:
          property_name (str): The name of the property

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        if property_name in self.__properties:
            del self.__properties[property_name]
            self._child_modified_callback()

        return self

    def create_relation(self, source, target, description, type, predicate, source_concept_name=None,
                        target_concept_name=None, confidence=1.0, directed=True):
        """

        Create a new property relation

        Args:
          source (str): Name of source property
          target (str): Name of target property
          description (str): Relation description, with property placeholders
          type (str): Relation type ('inter', 'intra', ...)
          predicate (str): free form predicate
          source_concept_name (str): Name of the source concept
          target_concept_name (str): Name of the target concept
          confidence (float): Relation confidence [0.0,1.0]
          directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance
        """

        if source not in self:
            raise KeyError('Cannot find property %s in event type %s.' %
                           (source, self.__attr['name']))

        if target not in self:
            raise KeyError('Cannot find property %s in event type %s.' %
                           (target, self.__attr['name']))

        if type in ('inter', 'intra'):
            if source_concept_name is None:
                if len(self[source].get_concept_associations()) == 0:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s properties of a %s while "
                        "the source property (%s) is not associated with any concepts." %
                        (type, source, target, self.get_display_name_singular(), source)
                    )

                if len(self[source].get_concept_associations()) > 1:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s of a %s while "
                        "the source property (%s) is associated with multiple concepts. Creation failed because "
                        "it was not specified  which concept to relate to." %
                        (type, source, target, self.get_display_name_singular(), source)
                    )

                source_concept_name = list(self[source].get_concept_associations().keys())[0]

            if target_concept_name is None:
                if len(self[target].get_concept_associations()) == 0:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s properties of a %s while "
                        "the target property (%s) is not associated with any concepts." %
                        (type, source, target, self.get_display_name_singular(), target)
                    )

                if len(self[target].get_concept_associations()) > 1:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s properties of a %s while "
                        "the target property (%s) is associated with multiple concepts. Creation failed because "
                        "it was not specified which concept to relate to." %
                        (type, source, target, self.get_display_name_singular(), target)
                    )

                target_concept_name = list(self[target].get_concept_associations().keys())[0]

        relation = edxml.ontology.PropertyRelation(
            self, self[source], self[target], self.__ontology.get_concept(source_concept_name, True),
            self.__ontology.get_concept(target_concept_name, True), description, type,
            predicate, confidence, directed
        )

        self.__relations[relation.get_persistent_id()] = relation.validate()

        self._child_modified_callback()
        return relation

    def add_relation(self, relation):
        """

        Add specified property relation. It is recommended to use the methods
        from the EventProperty class in stead, to create property relations using
        a syntax that yields more readable code.

        Args:
          relation (edxml.ontology.PropertyRelation): Property relation

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__relations[relation.get_persistent_id()] = relation.validate()

        self._child_modified_callback()
        return self

    def create_attachment(self, name):
        """

        Create a new attachment and add it to the event type. The description
        and singular display name are set to the attachment name. The plural
        form of the display name is constructed by appending an 's' to the
        singular form.

        Args:
            name (str): attachment name

        Returns:
            edxml.ontology.EventTypeAttachment
        """
        attachment = edxml.ontology.EventTypeAttachment(self, name)
        self.add_attachment(attachment)

        return attachment

    def add_attachment(self, attachment):
        """

        Add specified attachment definition to the event type.

        Args:
            attachment (edxml.ontology.EventTypeAttachment): attachment definition

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__attachments[attachment.get_name()] = attachment

        self._child_modified_callback()
        return self

    def make_children(self, siblings_description, parent):
        """

        Marks this event type as child of the specified parent event type. In
        case all unique properties of the parent also exist in the child, a
        default property mapping will be generated, mapping properties based
        on identical property names.

        Notes:
          You must call is_parent() on the parent before calling make_children()

        Args:
          siblings_description (str): EDXML siblings-description attribute
          parent (edxml.ontology.EventType): Parent event type

        Returns:
          edxml.ontology.EventTypeParent: The event type parent definition
        """

        if self.__parent_description:
            self.__parent = edxml.ontology.EventTypeParent(self, parent.get_name(), '', self.__parent_description,
                                                           siblings_description)
        else:
            raise Exception(
                'You must call is_parent() on the parent before calling make_children().')

        # If all unique properties of the parent event type
        # also exist in the child event type, we can create
        # a default property map.
        property_map = {}
        for propertyName, eventProperty in parent.get_unique_properties().items():
            if propertyName in self:
                property_map[propertyName] = propertyName
            else:
                property_map = {}
                break

        for childProperty, parentProperty in property_map.items():
            self.__parent.map(childProperty, parentProperty)

        self._child_modified_callback()
        return self.__parent

    def is_parent(self, parent_description, child):
        """

        Marks this event type as parent of the specified child event type.

        Notes:
          To be used in conjunction with the make_children() method.

        Args:
          parent_description (str): EDXML parent-description attribute
          child (edxml.ontology.EventType): Child event type

        Returns:
          edxml.ontology.EventType: The EventType instance

        """

        child.__parent_description = parent_description
        child._child_modified_callback()
        return self

    def set_description(self, description):
        """

        Sets the event type description

        Args:
          description (str): Description

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('description', str(description))
        return self

    def set_parent(self, parent):
        """

        Set the parent event type

        Notes:
          It is recommended to use the make_children() and
          is_parent() methods in stead whenever possible,
          which results in more readable code.

        Args:
          parent (edxml.ontology.EventTypeParent): Parent event type

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__parent = parent

        self._child_modified_callback()
        return self

    def add_class(self, class_name):
        """

        Adds the specified event type class

        Args:
          class_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        if class_name:
            if self.__attr['classlist'] == '':
                self._set_attr('classlist', class_name)
            else:
                self._set_attr('classlist', ','.join(
                    list(set(self.__attr['classlist'].split(',') + [class_name]))))
        return self

    def set_classes(self, class_names):
        """

        Replaces the list of classes that the event type
        belongs to with the specified list. Any duplicates
        are automatically removed from the list.

        Args:
          class_names (Iterable[str]):

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self._set_attr('classlist', ','.join(list(set(class_names))))
        return self

    def set_name(self, event_type_name):
        """

        Sets the name of the event type.

        Args:
         event_type_name (str): Event type name

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self._set_attr('name', event_type_name)
        return self

    def set_display_name(self, singular, plural=None):
        """

        Configure the display name. If the plural form
        is omitted, it will be auto-generated by
        appending an 's' to the singular form.

        Args:
          singular (str): Singular display name
          plural (str): Plural display name

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('display-name-singular', singular)
        self._set_attr('display-name-plural', plural or (singular + 's'))
        return self

    def set_summary_template(self, summary):
        """

        Set the event summary template

        Args:
          summary (str): The event summary template

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('summary', summary)
        return self

    def set_story_template(self, story):
        """

        Set the event story template. Newline characters are automatically
        replaced with [[NEWPAR:]] place holders.

        Args:
          story (str): The event story template

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('story', story.replace('\n', '[[NEWPAR:]]'))
        return self

    def set_version(self, version):
        """

        Sets the concept version

        Args:
          version (int): Version

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        self._set_attr('version', int(version))
        return self

    def set_timespan_property_name_start(self, property_name):
        """

        Sets the name of the property that defines the start of
        the time spans of the events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('timespan-start', property_name)
        return self

    def set_timespan_property_name_end(self, property_name):
        """

        Sets the name of the property that defines the end of
        the time spans of the events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('timespan-end', property_name)
        return self

    def evaluate_template(self, edxml_event, which='story', capitalize=True, colorize=False):
        """

        Evaluates the event story or summary template of an event type using
        specified event, returning the result.

        By default, the story template is evaluated, unless which is
        set to 'summary'.

        By default, we will try to capitalize the first letter of the resulting
        string, unless capitalize is set to False.

        Optionally, the output can be colorized. At his time this means that,
        when printed on the terminal, the objects in the evaluated string will
        be displayed using bold white characters.

        Args:
          edxml_event (edxml.EDXMLEvent): the EDXML event to use
          which (bool): which template to evaluate
          capitalize (bool): Capitalize output or not
          colorize (bool): Colorize output or not

        Returns:
          str:
        """

        # Recursively split a placeholder string at '{' and '}'
        def _split_template(template, offset=0):

            elements = []
            length = len(template)

            while offset < length:
                pos1 = template.find('{', offset)
                pos2 = template.find('}', offset)
                if pos1 == -1:
                    # There are no more sub-strings, Find closing bracket.
                    if pos2 == -1:
                        # No closing bracket either, which means that the
                        # remaining part of the string is one element.
                        # lacks brackets.
                        substring = template[offset:length]
                        offset = length
                        elements.append(substring)
                    else:
                        # Found closing bracket. Add substring and return
                        # to caller.
                        substring = template[offset:pos2]
                        offset = pos2 + 1
                        elements.append(substring)
                        break
                else:
                    # We found an opening bracket.

                    if pos2 == -1:
                        # No closing bracket
                        # Give up.
                        offset = length
                    else:
                        # We also found a closing bracket.

                        if pos1 < pos2:
                            # Opening bracket comes first, which means we should
                            # iterate.
                            substring = template[offset:pos1]
                            offset = pos1 + 1

                            elements.append(substring)
                            offset, parsed = _split_template(template, offset)
                            elements.append(parsed)
                        else:
                            # closing bracket comes first, which means we found
                            # an innermost substring. Add substring and return
                            # to caller.
                            substring = template[offset:pos2]
                            offset = pos2 + 1
                            elements.append(substring)
                            break

            return offset, elements

        def _format_time_duration(time_min, time_max):
            date_time_a = parse(time_min)
            date_time_b = parse(time_max)
            delta = relativedelta.relativedelta(date_time_b, date_time_a)

            if delta.minutes > 0:
                if delta.hours > 0:
                    if delta.days > 0:
                        if delta.months > 0:
                            if delta.years > 0:
                                return '%d years, %d months, %d days, %d hours, %d minutes and %d seconds' % \
                                       (delta.years, delta.months, delta.days,
                                        delta.hours, delta.minutes, delta.seconds)
                            else:
                                return '%d months, %d days, %d hours, %d minutes and %d seconds' % \
                                       (delta.months, delta.days, delta.hours,
                                        delta.minutes, delta.seconds)
                        else:
                            return '%d days, %d hours, %d minutes and %d seconds' % \
                                   (delta.days, delta.hours,
                                    delta.minutes, delta.seconds)
                    else:
                        return '%d hours, %d minutes and %d seconds' % \
                               (delta.hours, delta.minutes, delta.seconds)
                else:
                    return '%d minutes and %d seconds' % \
                           (delta.minutes, delta.seconds)
            else:
                return '%d.%d seconds' % \
                       (delta.seconds, delta.microseconds)

        def _format_byte_count(byte_count):
            suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
            if byte_count == 0:
                return '0 B'
            i = 0
            while byte_count >= 1024 and i < len(suffixes) - 1:
                byte_count /= 1024.
                i += 1
            f = ('%.2f' % byte_count).rstrip('0').rstrip('.')
            return '%s %s' % (f, suffixes[i])

        def _process_simple_placeholder_string(string, event_object_values, capitalize_string):

            replacements = {}

            if capitalize_string and string != '':
                if string[0] == '{':
                    if string[1:2] != '[[':
                        # Sting does not start with a placeholder,
                        # so we can safely capitalize.
                        string = string[0] + string[1].upper() + string[2:]
                else:
                    if string[0:1] != '[[':
                        # Sting does not start with a placeholder,
                        # so we can safely capitalize.
                        string = string[0].upper() + string[1:]

            # Match on placeholders like "[[FULLDATETIME:datetime]]", creating
            # groups of the strings in between the placeholders and the
            # placeholders themselves, with and without brackets included.
            placeholders = re.findall(r'(\[\[([^]]*)\]\])', string)

            # Format object values based on their data type to make them
            # more human friendly.
            for property_name, values in event_object_values.items():
                if self[property_name].get_data_type().get_family() == 'number':
                    if self[property_name].get_data_type().get_split()[1] in ('float', 'double'):
                        # Floating point numbers are normalized in scientific notation,
                        # here we format it to whatever is the most suitable for the value.
                        event_object_values[property_name] = {'%f' % float(value) for value in values}

            for placeholder in placeholders:

                object_strings = []
                try:
                    formatter, argument_string = placeholder[1].split(':', 1)
                    arguments = argument_string.split(',')
                except ValueError:
                    # No formatter present.
                    formatter = None
                    arguments = placeholder[1].split(',')

                if not formatter:
                    try:
                        object_strings.extend(event_object_values[arguments[0]])
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                elif formatter == 'TIMESPAN':

                    date_time_strings = []
                    for property_name in arguments:
                        try:
                            for object_value in event_object_values[property_name]:
                                date_time_strings.append(object_value)
                        except KeyError:
                            pass

                    if len(date_time_strings) > 0:
                        # Note that we use lexicographic sorting here.
                        date_time_a = parse(min(date_time_strings))
                        date_time_b = parse(max(date_time_strings))
                        object_strings.append('between %s and %s' % (
                            date_time_a.isoformat(' '), date_time_b.isoformat(' ')))
                    else:
                        # No valid replacement string could be generated, which implies
                        # that we must return an empty string.
                        return ''

                elif formatter == 'DURATION':

                    date_time_strings = []
                    for property_name in arguments:
                        try:
                            for object_value in event_object_values[property_name]:
                                date_time_strings.append(object_value)
                        except KeyError:
                            pass

                    if len(date_time_strings) > 0:
                        object_strings.append(_format_time_duration(
                            min(date_time_strings), max(date_time_strings)))
                    else:
                        # No valid replacement string could be generated, which implies
                        # that we must return an empty string.
                        return ''

                elif formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        date_time = parse(object_value)

                        try:
                            if formatter == 'FULLDATETIME':
                                object_strings.append(date_time.strftime(
                                    '%A, %B %d %Y at %H:%M:%Sh UTC'))
                            elif formatter == 'DATETIME':
                                object_strings.append(date_time.strftime(
                                    '%B %d %Y at %H:%M:%Sh UTC'))
                            elif formatter == 'DATE':
                                object_strings.append(
                                    date_time.strftime('%a, %B %d %Y'))
                            elif formatter == 'YEAR':
                                object_strings.append(date_time.strftime('%Y'))
                            elif formatter == 'MONTH':
                                object_strings.append(
                                    date_time.strftime('%B %Y'))
                            elif formatter == 'WEEK':
                                object_strings.append(
                                    date_time.strftime('week %W of %Y'))
                        except ValueError:
                            # This may happen for some time stamps before year 1900, which
                            # is not supported by strftime.
                            object_strings.append(
                                'some date, a long, long time ago')

                elif formatter == 'BYTECOUNT':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        object_strings.append(
                            _format_byte_count(int(object_value)))

                elif formatter == 'LATITUDE':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        degrees = int(object_value)
                        minutes = int((object_value - degrees) * 60.0)
                        seconds = int(
                            (object_value - degrees - (minutes / 60.0)) * 3600.0)

                        object_strings.append('%d°%d′%d %s″' % (
                            degrees, minutes, seconds, 'N' if degrees > 0 else 'S'))

                elif formatter == 'LONGITUDE':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        degrees = int(object_value)
                        minutes = int((object_value - degrees) * 60.0)
                        seconds = int(
                            (object_value - degrees - (minutes / 60.0)) * 3600.0)

                        object_strings.append('%d°%d′%d %s″' % (
                            degrees, minutes, seconds, 'E' if degrees > 0 else 'W'))

                elif formatter == 'UPPERCASE':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        object_strings.append(object_value.upper())

                elif formatter == 'CURRENCY':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    property_name, currency_symbol = arguments
                    for object_value in values:
                        object_strings.append('%.2f%s' % (
                            int(object_value), currency_symbol))

                elif formatter == 'URL':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    property_name, target_name = arguments
                    for object_value in values:
                        object_strings.append('%s (%s)' % (target_name, object_value))

                elif formatter == 'MERGE':

                    for property_name in arguments:
                        try:
                            for object_value in event_object_values[property_name]:
                                object_strings.append(object_value)
                        except KeyError:
                            pass

                elif formatter == 'COUNTRYCODE':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        try:
                            object_strings.append(
                                countries.get(object_value).name)
                        except KeyError:
                            object_strings.append(
                                object_value + ' (unknown country code)')

                elif formatter == 'BOOLEAN_STRINGCHOICE':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    property_name, true, false = arguments
                    for object_value in values:
                        if object_value == 'true':
                            object_strings.append(true)
                        else:
                            object_strings.append(false)

                elif formatter == 'BOOLEAN_ON_OFF':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        if object_value == 'true':
                            # Print 'on'
                            object_strings.append('on')
                        else:
                            # Print 'off'
                            object_strings.append('off')

                elif formatter == 'BOOLEAN_IS_ISNOT':

                    try:
                        values = event_object_values[arguments[0]]
                    except KeyError:
                        # Property has no object, which implies that
                        # we must produce an empty result.
                        return ''

                    for object_value in values:
                        if object_value == 'true':
                            # Print 'is'
                            object_strings.append('is')
                        else:
                            # Print 'is not'
                            object_strings.append('is not')

                elif formatter == 'EMPTY':

                    property_name = arguments[0]
                    if property_name not in event_object_values or len(event_object_values[property_name]) == 0:
                        # Property has no object, use the second formatter argument
                        # in stead of the object value itself.
                        object_strings.append(arguments[0])
                    else:
                        # Property has an object, so the formatter will
                        # yield an empty string. This in turn implies that
                        # we must produce an empty result.
                        return ''

                elif formatter == 'NEWPAR':

                    object_strings.append('\n')

                if len(object_strings) > 0:
                    if len(object_strings) > 1:
                        # If one property has multiple objects,
                        # list them all.
                        if ''.join(object_strings) != '':
                            last_object_value = object_strings.pop()
                            if colorize:
                                object_string = ', '.join(
                                    colored(ObjectString, 'white', attrs=['bold']) for ObjectString in object_strings)\
                                    + ' and ' + last_object_value
                            else:
                                object_string = ', '.join(object_strings)\
                                    + ' and ' + last_object_value
                        else:
                            object_string = ''
                    else:
                        if colorize and object_strings[0] != '':
                            object_string = colored(
                                object_strings[0], 'white', attrs=['bold'])
                        else:
                            object_string = object_strings[0]
                else:
                    object_string = ''

                replacements[placeholder[0]] = object_string

            # Return template where all placeholders are replaced
            # by the actual (formatted) object values

            for placeholder, replacement in replacements.items():
                if replacement == '':
                    # Placeholder produces empty string, which
                    # implies that we must produce an empty result.
                    return ''
                string = string.replace(placeholder, replacement)

            return string

        def _process_split_template(elements, event, capitalize, iteration_level=0):
            result = ''

            for Element in elements:
                if type(Element) == list:
                    processed = _process_split_template(Element, event, capitalize, iteration_level + 1)
                    capitalize = False
                else:
                    if Element != '':
                        processed = _process_simple_placeholder_string(
                            Element, event, capitalize)
                        capitalize = False
                    else:
                        processed = ''
                result += processed

            return result

        return _process_split_template(_split_template(self.__attr[which])[
            1], edxml_event.get_properties(), capitalize)

    def validate_template(self, template):
        """Checks if given template makes sense.

        Args:
          template (str): The template

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance

        """

        zero_argument_formatters = [
            'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'COUNTRYCODE', 'BOOLEAN_ON_OFF',
            'BOOLEAN_IS_ISNOT', 'UPPERCASE'
        ]

        # Test if template grammar is correct, by
        # checking that curly brackets are balanced.
        curly_nestings = {'{': 1, u'}': -1}
        nesting = 0
        for curly in [c for c in template if c in ['{', u'}']]:
            nesting += curly_nestings[curly]
            if nesting < 0:
                raise EDXMLValidationError(
                    'The following EDXML template contains unbalanced curly brackets:\n%s\n' % template)
        if nesting != 0:
            raise EDXMLValidationError(
                'The following EDXML template contains unbalanced curly brackets:\n%s\n' % template)

        placeholder_strings = re.findall(self.TEMPLATE_PATTERN, template)

        for template in placeholder_strings:
            # TODO: Write one generic check for existing properties by creating a table of
            # formatters, mapping formatter names to the indexes into the argument list of
            # arguments that are property names.
            try:
                formatter, argument_string = str(template).split(':', 1)
                arguments = argument_string.split(',')
            except ValueError:
                # Placeholder does not contain a formatter.
                if str(template) in self.__properties.keys():
                    continue
                else:
                    raise EDXMLValidationError(
                        'Event type %s contains a story or summary template which refers to one or more '
                        'nonexistent properties: %s' %
                        (self.__attr['name'], template)
                    )

            # Some kind of string formatter was used.
            # Figure out which one, and check if it
            # is used correctly.
            if formatter in ['DURATION', 'TIMESPAN']:

                if len(arguments) != 2:
                    raise EDXMLValidationError(
                        ('Event type %s contains a story or summary template containing a string formatter (%s) '
                         'which requires two properties, but %d properties were specified.') %
                        (self.__attr['name'], formatter, len(arguments))
                    )

                if arguments[0] in self.__properties.keys() and \
                   arguments[1] in self.__properties.keys():

                    # Check that both properties are datetime values
                    for propertyName in arguments:
                        if propertyName == '':
                            raise EDXMLValidationError(
                                'Invalid property name in %s formatter: "%s"' % (propertyName, formatter))
                        if str(self.__properties[propertyName].get_data_type()) != 'datetime':
                            raise EDXMLValidationError(
                                ('Event type %s contains a story or summary template which '
                                 'uses a time related formatter, '
                                 'but the used property (%s) is not a datetime value.') % (
                                    self.__attr['name'], propertyName)
                            )

                    continue
            else:
                if formatter not in self.KNOWN_FORMATTERS:
                    raise EDXMLValidationError(
                        'Event type %s contains a story or summary template which refers to an unknown formatter: %s' %
                        (self.__attr['name'], formatter)
                    )

                if formatter in ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']:
                    # Check that only one property is specified after the formatter
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            ('Event type %s contains a story or summary template which uses the %s formatter, '
                             'which accepts just one property. Multiple properties were specified: %s') % (
                                self.__attr['name'], formatter, argument_string)
                        )
                    # Check that property is a datetime value
                    if argument_string == '':
                        raise EDXMLValidationError(
                            'Invalid property name in %s formatter: "%s"' % (
                                argument_string, formatter)
                        )
                    if str(self.__properties[argument_string].get_data_type()) != 'datetime':
                        raise EDXMLValidationError(
                            ('Event type %s contains a template which uses the %s formatter. '
                             'The used property (%s) is not a datetime value, though.') % (
                                self.__attr['name'], formatter, argument_string)
                        )

                elif formatter in zero_argument_formatters:
                    # Check that no additional arguments are present
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            ('Event type %s contains a story or summary template which uses the %s formatter. '
                             'This formatter accepts no arguments, but they were specified: %s') %
                            (self.__attr['name'], formatter, template)
                        )
                    # Check that only one property is specified after the formatter
                    if len(arguments) > 1:
                        raise EDXMLValidationError(
                            ('Event type %s contains a story or summary template which uses the %s formatter. '
                             'This formatter accepts just one property. Multiple properties were given though: %s')
                            % (self.__attr['name'], formatter, argument_string)
                        )
                    if formatter in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
                        # Check that property is a boolean
                        if argument_string == '':
                            raise EDXMLValidationError(
                                'Invalid property name in %s formatter: "%s"' % (
                                    argument_string, formatter)
                            )
                        if str(self.__properties[argument_string].get_data_type()) != 'boolean':
                            raise EDXMLValidationError(
                                ('Event type %s contains a story or summary template which uses the %s formatter. '
                                 'The used property (%s) is not a boolean, though.') %
                                (self.__attr['name'], formatter, argument_string)
                            )

                elif formatter == 'CURRENCY':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Event type %s contains a story or summary template which uses a '
                            'malformed %s formatter: %s' %
                            (self.__attr['name'], formatter, template)
                        )

                elif formatter == 'URL':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Event type %s contains a story or summary template which uses a '
                            'malformed %s formatter: %s' %
                            (self.__attr['name'], formatter, template)
                        )

                elif formatter == 'EMPTY':
                    if len(arguments) != 2:
                        raise EDXMLValidationError(
                            'Event type %s contains a story or summary template which uses a '
                            'malformed %s formatter: %s' %
                            (self.__attr['name'], formatter, template)
                        )

                elif formatter == 'NEWPAR':
                    if len(arguments) != 1 or arguments[0] != '':
                        raise EDXMLValidationError(
                            'Event type %s contains a story or summary template which uses a '
                            'malformed %s formatter: %s' %
                            (self.__attr['name'], formatter, template)
                        )

                elif formatter == 'BOOLEAN_STRINGCHOICE':
                    if len(arguments) != 3:
                        raise EDXMLValidationError(
                            'Event type %s contains a story or summary template which uses a '
                            'malformed %s formatter: %s' %
                            (self.__attr['name'], formatter, template)
                        )
                    # Check that property is a boolean
                    if argument_string == '':
                        raise EDXMLValidationError(
                            'Invalid property name in %s formatter: "%s"' % (
                                argument_string, formatter)
                        )
                    if str(self.__properties[arguments[0]].get_data_type()) != 'boolean':
                        raise EDXMLValidationError(
                            ('Event type %s contains a story or summary template which uses the %s formatter. '
                             'The used property (%s) is not a boolean, though.') %
                            (self.__attr['name'], formatter, argument_string)
                        )

                elif formatter == 'MERGE':
                    # No special requirements to check for
                    pass

                else:
                    raise EDXMLValidationError(
                        'Event type %s contains a story or summary template which uses an unknown formatter: %s' %
                        (self.__attr['name'], formatter)
                    )

        return self

    def validate(self):
        """

        Checks if the event type definition is valid. Since it does
        not have access to the full ontology, the context of
        the event type is not considered. For example, it does not
        check if the event type definition refers to a parent event
        type that actually exists. Also, templates are not validated.

        Raises:
          EDXMLValidationError
        Returns:
          EventType: The EventType instance

        """
        if not len(self.__attr['name']) <= 64:
            raise EDXMLValidationError(
                'The name of event type "%s" is too long.' % self.__attr['name'])
        if not re.match(self.NAME_PATTERN, self.__attr['name']):
            raise EDXMLValidationError(
                'Event type "%s" has an invalid name.' % self.__attr['name'])

        if not len(self.__attr['display-name-singular']) <= 32:
            raise EDXMLValidationError(
                'The singular display name of event type "%s" is too long: "%s"' % (
                    self.__attr['name'], self.__attr['display-name-singular'])
            )

        if not len(self.__attr['display-name-plural']) <= 32:
            raise EDXMLValidationError(
                'The plural display name of event type "%s" is too long: "%s"' % (
                    self.__attr['name'], self.__attr['display-name-plural'])
            )

        if normalize_xml_token(self.__attr['display-name-singular']) != self.__attr['display-name-singular']:
            raise EDXMLValidationError(
                'The singular display name of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['display-name-singular'])
            )

        if normalize_xml_token(self.__attr['display-name-plural']) != self.__attr['display-name-plural']:
            raise EDXMLValidationError(
                'The plural display name of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['display-name-plural'])
            )

        if normalize_xml_token(self.__attr['description']) != self.__attr['description']:
            raise EDXMLValidationError(
                'The description of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['description'])
            )

        if not len(self.__attr['description']) <= 128:
            raise EDXMLValidationError(
                'The description of event type "%s" is too long: "%s"' % (
                    self.__attr['name'], self.__attr['description'])
            )

        if normalize_xml_token(self.__attr['classlist']) != self.__attr['classlist']:
            raise EDXMLValidationError(
                'The class list of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['classlist'])
            )

        if self.__attr['classlist'] and not re.match(self.CLASS_LIST_PATTERN, self.__attr['classlist']):
            raise EDXMLValidationError(
                'Event type "%s" has an invalid class list: "%s"' %
                (self.__attr['name'], self.__attr['classlist'])
            )

        if self.__attr['timespan-start'] is not None:
            if not self.__attr['timespan-start'] in self.get_properties().keys():
                raise EDXMLValidationError(
                    'Event type "%s" defines the start of its event time spans '
                    'by means of property "%s", which does not exist.' %
                    (self.__attr['name'], self.__attr['timespan-start'])
                )
            if not self.get_properties()[self.__attr['timespan-start']].get_data_type().is_datetime():
                raise EDXMLValidationError(
                    'Event type "%s" defines the start of its event time spans '
                    'by means of property "%s", which does not have a datetime data type.' %
                    (self.__attr['name'], self.__attr['timespan-start'])
                )

        if self.__attr['timespan-end'] is not None:
            if not self.__attr['timespan-end'] in self.get_properties().keys():
                raise EDXMLValidationError(
                    'Event type "%s" defines the end of its event time spans '
                    'by means of property "%s", which does not exist.' %
                    (self.__attr['name'], self.__attr['timespan-end'])
                )
            if not self.get_properties()[self.__attr['timespan-end']].get_data_type().is_datetime():
                raise EDXMLValidationError(
                    'Event type "%s" defines the end of its event time spans '
                    'by means of property "%s", which does not have a datetime data type.' %
                    (self.__attr['name'], self.__attr['timespan-end'])
                )

        if normalize_xml_token(self.__attr['story']) != self.__attr['story']:
            raise EDXMLValidationError(
                'The story template of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['story'])
            )

        if normalize_xml_token(self.__attr['summary']) != self.__attr['summary']:
            raise EDXMLValidationError(
                'The summary template of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__attr['name'], self.__attr['summary'])
            )

        self.validate_template(self.__attr['summary'])
        self.validate_template(self.__attr['story'])

        for propertyName, eventProperty in self.get_properties().items():
            eventProperty.validate()

        for relation in self.__relations.values():
            relation.validate()

        for attachment in self.__attachments.values():
            attachment.validate()

        return self

    @classmethod
    def create_from_xml(cls, type_element, ontology):
        event_type = cls(
            ontology,
            type_element.attrib['name'],
            type_element.attrib['display-name-singular'],
            type_element.attrib['display-name-plural'],
            type_element.attrib['description'],
            type_element.attrib.get('classlist', ''),
            type_element.attrib['summary'],
            type_element.attrib['story']
        ).set_version(type_element.attrib['version'])\
         .set_timespan_property_name_start(type_element.attrib.get('timespan-start'))\
         .set_timespan_property_name_end(type_element.attrib.get('timespan-end'))

        for element in type_element:
            if element.tag == '{http://edxml.org/edxml}parent':
                event_type.set_parent(
                    edxml.ontology.EventTypeParent.create_from_xml(element, event_type))
            elif element.tag == '{http://edxml.org/edxml}properties':
                for propertyElement in element:
                    event_type.add_property(
                        edxml.ontology.EventProperty.create_from_xml(propertyElement, ontology, event_type))

            elif element.tag == '{http://edxml.org/edxml}relations':
                for relationElement in element:
                    event_type.add_relation(
                        edxml.ontology.PropertyRelation.create_from_xml(relationElement, event_type, ontology))

            elif element.tag == '{http://edxml.org/edxml}attachments':
                for attachmentElement in element:
                    event_type.add_attachment(
                        edxml.ontology.EventTypeAttachment.create_from_xml(attachmentElement, event_type))

        return event_type

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        other_is_newer = other.get_version() > self.get_version()
        versions_differ = other.get_version() != self.get_version()

        if other_is_newer:
            new = other
            old = self
        else:
            new = self
            old = other

        old.validate()
        new.validate()

        equal = not versions_differ
        is_valid_upgrade = True

        if old.get_name() != new.get_name():
            raise ValueError("Event types with different names are not comparable.")

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        equal &= old.get_display_name_singular() == new.get_display_name_singular()
        equal &= old.get_display_name_plural() == new.get_display_name_plural()
        equal &= old.get_description() == new.get_description()
        equal &= old.get_summary_template() == new.get_summary_template()
        equal &= old.get_story_template() == new.get_story_template()

        # Check for illegal upgrade paths:

        if old.get_parent() is None and new.get_parent() is not None:
            # New version adds a parent.
            equal = False

        if new.get_parent() is None and old.get_parent() is not None:
            # New version is missing the parent definition that
            # the old one has. No upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_properties().keys() != new.get_properties().keys():
            # Adding a property is possible, removing one is not.
            equal = False
            missing_property_names = set(old.get_properties().keys()) - set(new.get_properties().keys())
            new_property_names = set(new.get_properties().keys()) - set(old.get_properties().keys())
            is_valid_upgrade &= versions_differ and len(missing_property_names) == 0

            for property_name in new_property_names:
                # Newly added properties must be optional.
                is_valid_upgrade &= new.get_properties()[property_name].is_optional()
                # A timeless event type must remain timeless.
                if old.is_timeless():
                    is_valid_upgrade &= new.is_timeless()

        if old.get_property_relations().keys() != new.get_property_relations().keys():
            # Adding a relation is possible, removing one is not.
            equal = False
            missing_relation_ids = set(old.get_property_relations().keys()) - set(new.get_property_relations().keys())
            is_valid_upgrade &= versions_differ and len(missing_relation_ids) == 0

        if set(old.get_attachments().keys()) - set(new.get_attachments().keys()) != set():
            # New version removes attachments. No upgrade possible.
            equal = is_valid_upgrade = False

        if set(old.get_classes()) != set(new.get_classes()):
            # Adding an event type class is possible, removing one is not.
            equal = False
            is_valid_upgrade &= versions_differ and len(set(old.get_classes()) - set(new.get_classes())) == 0

        if old.get_timespan_property_name_start() != new.get_timespan_property_name_start():
            # Versions do not agree on their timespan definitions. No upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_timespan_property_name_end() != new.get_timespan_property_name_end():
            # Versions do not agree on their timespan definitions. No upgrade possible.
            equal = is_valid_upgrade = False

        # Check upgrade paths for sub-elements:

        if old.get_parent() is not None and new.get_parent() is not None:
            if old.get_parent() != new.get_parent():
                # Parent definitions differ, check that new definition is
                # a valid upgrade of the old definition.
                equal = False
                is_valid_upgrade &= new.get_parent() > old.get_parent()

        for property_name, property in new.get_properties().items():
            if property_name in old:
                if old[property_name] != new[property_name]:
                    # Property definitions differ, check that new definition is
                    # a valid upgrade of the old definition.
                    equal = False
                    is_valid_upgrade &= new[property_name] > old[property_name]

        for relation_id, relation in new.get_property_relations().items():
            if relation_id in old.get_property_relations():
                if new.get_property_relations()[relation_id] != old.get_property_relations()[relation_id]:
                    # Relation definitions differ, check that new definition is
                    # a valid upgrade of the old definition.
                    equal = False
                    is_valid_upgrade &= \
                        new.get_property_relations()[relation_id] > old.get_property_relations()[relation_id]

        for name, attachment in new.get_attachments().items():
            if name in old.get_attachments():
                if new.get_attachments()[name] != old.get_attachments()[name]:
                    # Attachment definitions differ, check that new definition is
                    # a valid upgrade of the old definition.
                    equal = False
                    is_valid_upgrade &= \
                        new.get_attachments()[name] > old.get_attachments()[name]

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        raise EDXMLValidationError(
            "Event type definitions are neither equal nor valid upgrades / downgrades of one another "
            "due to the following difference in their definitions:\nOld version:\n{}\nNew version:\n{}".format(
                etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
                etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
            )
        )

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, event_type):
        """

        Updates the event type to match the EventType
        instance passed to this method, returning the
        updated instance.

        Args:
          event_type (edxml.ontology.EventType): The new EventType instance

        Returns:
          edxml.ontology.EventType: The updated EventType instance

        """
        if not isinstance(event_type, type(self)):
            raise TypeError("Can only update using an ontology element of the same type.")

        if event_type > self:
            # The new definition is indeed newer. Update self.

            if event_type.get_parent() is not None:
                if self.get_parent() is not None:
                    self.get_parent().update(event_type.get_parent())
                else:
                    self.set_parent(event_type.get_parent())

            for property_name, property in self.get_properties().items():
                self[property_name].update(event_type[property_name])

            for property_name in set(event_type.get_properties().keys()) - set(self.get_properties().keys()):
                self.add_property(event_type.get_properties()[property_name])

            for relation_id, relation in self.get_property_relations().items():
                self.get_property_relations()[relation_id].update(event_type.get_property_relations()[relation_id])

            for relation_id in set(event_type.get_property_relations().keys()) - \
                    set(self.get_property_relations().keys()):
                self.add_relation(event_type.get_property_relations()[relation_id])

            for attachment_name, attachment in event_type.get_attachments().items():
                if attachment_name in self.get_attachments().keys():
                    self.get_attachments()[attachment_name].update(event_type.get_attachments()[attachment_name])
                else:
                    self.add_attachment(attachment)

            self.set_description(event_type.get_description())
            self.set_display_name(event_type.get_display_name_singular(), event_type.get_display_name_plural())
            self.set_summary_template(event_type.get_summary_template())
            self.set_story_template(event_type.get_story_template())
            self.set_classes(set(self.get_classes()).union(event_type.get_classes()))
            self.set_version(event_type.get_version())

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <eventtype> tag for this event type.

        Returns:
          etree.Element: The element

        """
        attribs = dict(self.__attr)
        attribs['version'] = str(attribs['version'])

        if attribs['classlist'] == '':
            del attribs['classlist']

        element = etree.Element('eventtype', {k: v for k, v in attribs.items() if v})
        if self.__parent:
            element.append(self.__parent.generate_xml())

        properties = etree.Element('properties')
        for property_name in sorted(self.__properties.keys()):
            properties.append(self.__properties[property_name].generate_xml())
        element.append(properties)

        if len(self.__relations) > 0:
            relations = etree.Element('relations')
            for relation_id in sorted(self.__relations.keys()):
                relations.append(self.__relations[relation_id].generate_xml())
            element.append(relations)

        if len(self.__attachments) > 0:
            attachments = etree.Element('attachments')
            for attachment_name in sorted(self.__attachments.keys()):
                attachments.append(self.__attachments[attachment_name].generate_xml())
            element.append(attachments)

        return element

    def get_singular_property_names(self):
        """

        Returns a list of properties that cannot have multiple values.

        Returns:
           list(str): List of property names
        """
        return [property_name for property_name, prop in self.__properties.items() if prop.is_single_valued()]

    def get_mandatory_property_names(self):
        """

        Returns a list of properties that must have a value

        Returns:
           list(str): List of property names
        """
        return [property_name for property_name, prop in self.__properties.items() if prop.is_mandatory()]

    def validate_event_structure(self, edxml_event):
        """

        Validates the structure of the event by comparing its
        properties and their object count to the requirements
        of the event type. Generates exceptions that are much
        more readable than standard XML validation exceptions.

        Args:
          edxml_event (edxml.EDXMLEvent):

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        if self.get_parent() is not None:
            parent_property_mapping = self.get_parent().get_property_map()
        else:
            parent_property_mapping = {}

        for property_name, objects in edxml_event.items():

            if property_name in parent_property_mapping and len(objects) > 1:
                raise EDXMLValidationError(
                    ('An event of type %s contains multiple objects of property %s, '
                     'but this property can only have one object due to it being used '
                     'in an implicit parent definition.') % (self.__attr['name'], property_name)
                )

            # Check if the property is actually
            # supposed to be in this event.
            if property_name not in self.get_properties():
                raise EDXMLValidationError(
                    ('An event of type %s contains an object of property %s, '
                     'but this property does not belong to the event type.') %
                    (self.__attr['name'], property_name)
                )

        # Verify that match, min and max properties have an object.
        for property_name in self.get_mandatory_property_names():
            if property_name not in edxml_event:
                raise EDXMLValidationError(
                    ('An event of type %s is missing an object for property %s, '
                     'while it must have an object due to its configured merge strategy.')
                    % (self.__attr['name'], property_name)
                )

        # Verify that properties that cannot have multiple
        # objects actually have at most one object
        for property_name in self.get_singular_property_names():
            if property_name in edxml_event:
                if len(edxml_event[property_name]) > 1:
                    raise EDXMLValidationError(
                        ('An event of type %s has multiple objects of property %s, '
                         'while it cannot have more than one due to its configured merge strategy '
                         'or due to a implicit parent definition.') %
                        (self.__attr['name'], property_name)
                    )

        return self

    def validate_event_objects(self, event):
        """

        Validates the object values in the event by comparing
        the values with their data types. Generates exceptions
        that are much more readable than standard XML validation
        exceptions.

        Args:
          event (edxml.EDXMLEvent):

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        for propertyName, objects in event.items():

            property_object_type = self.__properties[propertyName].get_object_type()

            for objectValue in objects:
                try:
                    property_object_type.validate_object_value(objectValue)
                except EDXMLValidationError as e:
                    raise EDXMLValidationError(
                        'Invalid value for property %s of event type %s: %s' % (
                            propertyName, self.__attr['name'], e)
                    )

        return self

    def validate_event_attachments(self, event):
        for name, attachment in event.get_attachments().items():
            if name not in self.get_attachments().keys():
                raise EDXMLValidationError(
                    'Event type %s has no attachment named %s.' % (self.__attr['name'], name)
                )

    def normalize_event_objects(self, event):
        """

        Normalizes the object values in the event, resulting in
        valid EDXML object value strings. Raises an exception
        in case an object value cannot be normalized.

        Args:
          event (edxml.EDXMLEvent):

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        for propertyName, objects in event.items():

            try:
                property_object_type = self.__properties[propertyName].get_object_type()
            except KeyError:
                raise EDXMLValidationError("Event type '%s' has no property '%s'." % (self.get_name(), propertyName))

            try:
                event[propertyName] = property_object_type.get_data_type(
                ).normalize_objects(objects)
            except EDXMLValidationError as e:
                raise EDXMLValidationError(
                    'Invalid value for property %s of event type %s: %s' % (
                        propertyName, self.__attr['name'], e)
                )

        return self

    def generate_relax_ng(self, ontology, namespaced=True):
        """

        Returns an ElementTree containing a RelaxNG schema for validating
        events of this event type. It requires an Ontology instance for
        obtaining the definitions of objects types referred to by the
        properties of the event type.

        By default, the schema expects the events to be namespaced. This can
        be turned off for validating events that will be added into an EDXML
        data stream that has a default namespace that events will inherit.

        Args:
          ontology (edxml.ontology.Ontology): Ontology containing the event type
          namespaced (bool): Require a namespace specification or not

        Returns:
          lxml.etree.RelaxNG: The schema
        """
        e = ElementMaker()

        # Define a recursive 'anything' pattern
        anything = e.zeroOrMore(
            e.choice(
                e.element(
                    e.anyName(),
                    e.ref(name='anything')
                ),
                e.attribute(
                    e.anyName()
                )
            )
        )

        # Use the 'anything' pattern to define a pattern
        # that allows any element attributes as long as they
        # have a namespace that is not the EDXML namespace.
        # We will use that pattern in the event definition.
        foreign_attribs = e.zeroOrMore(
            e.attribute(
                e.anyName(
                    getattr(e, 'except')(
                        e.nsName(ns=''),
                        e.nsName(ns='http://edxml.org/edxml')
                    )
                )
            )
        )

        properties = []

        for property_name, event_property in self.__properties.items():
            object_type = ontology.get_object_type(event_property.get_object_type_name())
            if property_name in self.get_mandatory_property_names():
                if property_name in self.get_singular_property_names():
                    # Exactly one object must be present, no need
                    # to wrap it into an element to indicate this.
                    properties.append(
                        e.element(object_type.generate_relaxng(), name=property_name))
                else:
                    # Property is mandatory and can have any
                    # number of objects.
                    properties.append(e.oneOrMore(
                        e.element(object_type.generate_relaxng(), name=property_name)))
            else:
                if property_name in self.get_singular_property_names():
                    # Property is not mandatory, but if present there
                    # cannot be multiple values.
                    properties.append(e.optional(
                        e.element(object_type.generate_relaxng(), name=property_name)))
                else:
                    # Property is not mandatory and can have any
                    # number of objects.
                    properties.append(e.zeroOrMore(
                        e.element(object_type.generate_relaxng(), name=property_name)))

        attachments = []
        for attachment_name, attachment in self.get_attachments().items():
            if attachment.is_base64_string():
                attachments.append(
                    e.optional(
                        e.element(
                            e.data('', type='base64Binary'),
                            name=attachment_name
                        )
                    )
                )
            else:
                attachments.append(
                    e.optional(
                        e.element(e.text(), name=attachment_name)
                    )
                )

        schema = e.element(
            e.ref(name='foreign-attributes'),
            e.attribute(
                e.data(
                    e.param('1', name='minLength'),
                    e.param('64', name='maxLength'),
                    e.param('[a-z0-9.-]*', name='pattern'),
                    type='token'
                ),
                name='event-type'
            ),
            e.attribute(
                e.data(
                    e.param('1', name='minLength'),
                    e.param('(/[a-z0-9-]+)*/', name='pattern'),
                    type='token'
                ),
                name='source-uri'
            ),
            e.optional(
                e.attribute(
                    e.data(
                        e.param(
                            '([0-9a-f]{40})(,[0-9a-f]{40})*', name='pattern'),
                        type='normalizedString'),
                    name='parents'
                )
            ),
            e.element(
                e.interleave(*properties),
                name='properties'
            ) if len(properties) > 0 else e.element(e.empty, name='properties'),
            e.optional(
                e.element(
                    e.interleave(*attachments),
                    name='attachments'
                ) if len(attachments) > 0 else e.element(e.empty, name='attachments'),
            ),
            name='event',
            **{'ns': 'http://edxml.org/edxml'} if namespaced else {}
        )

        schema = e.grammar(
            e.start(
                schema
            ),
            e.define(
                anything,
                name='anything'
            ),
            e.define(
                foreign_attribs,
                name='foreign-attributes'
            ),
            xmlns='http://relaxng.org/ns/structure/1.0',
            datatypeLibrary='http://www.w3.org/2001/XMLSchema-datatypes',
        )

        # Note that, for some reason, using a programmatically built ElementTree
        # to instantiate a RelaxNG object fails with 'schema is empty'. If we
        # convert the schema to a string and parse it back gain, all is good.
        return etree.parse(BytesIO(etree.tostring(etree.ElementTree(schema))))
