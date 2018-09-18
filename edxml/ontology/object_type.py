# -*- coding: utf-8 -*-

import re
import sre_constants

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import DataType, OntologyElement


class ObjectType(OntologyElement):
    """
    Class representing an EDXML object type
    """

    NAME_PATTERN = re.compile('^[a-z0-9.]{1,64}$')
    DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
    FUZZY_MATCHING_PATTERN = re.compile(
        r"^(none)|(phonetic)|(substring:.*)|(\[[0-9]{1,2}:\])|(\[:[0-9]{1,2}\])$")

    def __init__(self, ontology, name, display_name=None, description=None, data_type='string:0:cs:u', compress=False,
                 fuzzy_matching='none', regexp=r'[\s\S]*'):

        self.__attr = {
            'name': name,
            'display-name': display_name or ' '.join(('%s/%s' % (name, name)).split('.')),
            'description': description or name,
            'data-type': data_type,
            'compress': bool(compress),
            'fuzzy-matching': fuzzy_matching,
            'regexp': regexp,
            'version': 1
        }

        self.__ontology = ontology  # type: edxml.ontology.Ontology

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__ontology._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def get_name(self):
        """

        Returns the name of the object type.

        Returns:
          str: The object type name
        """

        return self.__attr['name']

    def get_display_name(self):
        """

        Returns the display-name attribute of the object type.

        Returns:
          str:
        """

        return self.__attr['display-name']

    def get_display_name_singular(self):
        """

        Returns the display name of the object type, in singular form.

        Returns:
          str:
        """

        return self.__attr['display-name'].split('/')[0]

    def get_display_name_plural(self):
        """

        Returns the display name of the object type, in plural form.

        Returns:
          str:
        """

        return self.__attr['display-name'].split('/')[1]

    def get_description(self):
        """

        Returns the description of the object type.

        Returns:
          str:
        """

        return self.__attr['description']

    def get_data_type(self):
        """

        Returns the data type of the object type.

        Returns:
          edxml.ontology.DataType: The data type
        """

        return DataType(self.__attr['data-type'])

    def is_compressible(self):
        """

        Returns True if compression is advised for the object type,
        returns False otherwise.

        Returns:
          bool:
        """

        return self.__attr['compress']

    def get_fuzzy_matching(self):
        """

        Returns the EDXML fuzzy-matching attribute for the object type.

        Returns:
          str:
        """

        return self.__attr['fuzzy-matching']

    def get_regexp(self):
        """

        Returns the regular expression that object values must match.

        Returns:
          str:
        """

        return self.__attr['regexp']

    def get_version(self):
        """

        Returns the version of the source definition.

        Returns:
          int:
        """

        return self.__attr['version']

    def set_description(self, description):
        """

        Sets the object type description

        Args:
          description (str): Description

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """

        self._set_attr('description', str(description))
        return self

    def set_data_type(self, data_type):
        """

        Configure the data type.

        Args:
          data_type (edxml.ontology.DataType): DataType instance

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('data-type', str(data_type))
        return self

    def set_display_name(self, singular, plural=None):
        """

        Configure the display name. If the plural form
        is omitted, it will be auto-generated by
        appending an 's' to the singular form.

        Args:
          singular (str): display name (singular form)
          plural (str): display name (plural form)

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """

        if plural is None:
            plural = '%ss' % singular

        self._set_attr('display-name', '%s/%s' % (singular, plural))
        return self

    def set_regexp(self, pattern):
        """

        Configure a regular expression that object
        values must match.

        Args:
          pattern (str): Regular expression

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('regexp', str(pattern))
        return self

    def set_fuzzy_matching_attribute(self, attribute):
        """

        Sets the EDXML fuzzy-matching attribute.

        Notes:
          It is recommended to use the FuzzyMatch...() methods
          in stead to configure fuzzy matching.

        Args:
          attribute (str): The attribute value

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('fuzzy-matching', attribute)
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

    def fuzzy_match_head(self, length):
        """

        Configure fuzzy matching on the head of the string
        (only for string data types).

        Args:
          length (int): Number of characters to match

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('fuzzy-matching', '[%d:]' % int(length))
        return self

    def fuzzy_match_tail(self, length):
        """

        Configure fuzzy matching on the tail of the string
        (only for string data types).

        Args:
          length (int): Number of characters to match

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('fuzzy-matching', '[:%d]' % int(length))
        return self

    def fuzzy_match_substring(self, pattern):
        """

        Configure fuzzy matching on a substring
        (only for string data types).

        Args:
          pattern (str): Regular expression

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('fuzzy-matching', 'substring:%s' % str(pattern))
        return self

    def fuzzy_match_phonetic(self):
        """

        Configure fuzzy matching on the sound
        of the string (phonetic fingerprinting).

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('fuzzy-matching', 'phonetic')
        return self

    def compress(self, is_compressible=True):
        """

        Enable or disable compression for the object type.

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('compress', is_compressible)
        return self

    def generate_relaxng(self):

        return DataType(self.__attr['data-type']).generate_relaxng(self.__attr['regexp'])

    def validate_object_value(self, value):
        """

        Validates the provided object value against
        the object type definition as well as its
        data type, raising an EDXMLValidationException
        when the value is invalid.

        Args:
          value (unicode): Object value

        Raises:
          EDXMLValidationError

        Returns:
           edxml.ontology.ObjectType: The ObjectType instance
        """

        # First, validate against data type
        self.get_data_type().validate_object_value(value)

        # Validate against object type specific restrictions,
        # like the regular expression.
        split_data_type = self.__attr['data-type'].split(':')

        if split_data_type[0] == 'string':
            if len(split_data_type) >= 4 and 'i' in split_data_type[3]:
                # Perform regex matching on lower case string
                value = value.lower()
            if not re.match(self.__attr['regexp'], value):
                raise EDXMLValidationError(
                    "Object value '%s' of object type %s does not match regexp '%s' of the object type."
                    % (value, self.__attr['name'], self.__attr['regexp'])
                )

    def validate(self):
        """

        Checks if the object type is valid. It only looks
        at the attributes of the definition itself. Since it does
        not have access to the full ontology, the context of
        the event type is not considered. For example, it does not
        check if other, conflicting object type definitions exist.

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance

        """
        if not len(self.__attr['name']) <= 64:
            raise EDXMLValidationError(
                'The name of object type "%s" is too long.' % self.__attr['name'])
        if not re.match(self.NAME_PATTERN, self.__attr['name']):
            raise EDXMLValidationError(
                'Object type "%s" has an invalid name.' % self.__attr['name'])

        if not len(self.__attr['display-name']) <= 64:
            raise EDXMLValidationError(
                'The display name of object type "%s" is too long: "%s".' % (
                    self.__attr['name'], self.__attr['display-name'])
            )
        if not re.match(self.DISPLAY_NAME_PATTERN, self.__attr['display-name']):
            raise EDXMLValidationError(
                'Object type "%s" has an invalid display name: "%s"' % (
                    self.__attr['name'], self.__attr['display-name'])
            )

        if not len(self.__attr['description']) <= 128:
            raise EDXMLValidationError(
                'The description of object type "%s" is too long: "%s"' % (
                    self.__attr['name'], self.__attr['description'])
            )

        if not re.match(self.FUZZY_MATCHING_PATTERN, self.__attr['fuzzy-matching']):
            raise EDXMLValidationError(
                'Object type "%s" has an invalid fuzzy-matching attribute: "%s"' % (
                    self.__attr['name'], self.__attr['fuzzy-matching'])
            )
        if self.__attr['fuzzy-matching'][:10] == 'substring:':
            try:
                re.compile('%s' % self.__attr['fuzzy-matching'][10:])
            except sre_constants.error:
                raise EDXMLValidationError(
                    'Definition of object type %s has an invalid regular expression in its '
                    'fuzzy-matching attribute: "%s"' % (
                        (self.__attr['name'], self.__attr['fuzzy-matching'])))

        if type(self.__attr['compress']) != bool:
            raise EDXMLValidationError(
                'Object type "%s" has an invalid compress attribute: "%s"' % (
                    self.__attr['name'], repr(self.__attr['compress']))
            )

        try:
            re.compile(self.__attr['regexp'])
        except sre_constants.error:
            raise EDXMLValidationError('Object type "%s" contains invalid regular expression: "%s"' %
                                       (self.__attr['name'], self.__attr['regexp']))

        DataType(self.__attr['data-type']).validate()

        return self

    @classmethod
    def create_from_xml(cls, type_element, ontology):
        return cls(
            ontology,
            type_element.attrib['name'],
            type_element.attrib['display-name'],
            type_element.attrib['description'],
            type_element.attrib['data-type'],
            type_element.get('compress', 'false') == 'true',
            type_element.get('fuzzy-matching', 'none'),
            type_element.get('regexp', r'[\s\S]*')
        ).set_version(type_element.attrib['version'])

    def update(self, object_type):
        """

        Args:
          object_type (edxml.ontology.ObjectType): The new ObjectType instance

        Returns:
          edxml.ontology.ObjectType: The updated ObjectType instance

        """
        if self.__attr['name'] != object_type.get_name():
            raise Exception('Attempt to update object type "%s" with object type "%s".' %
                            (self.__attr['name'], object_type.get_name()))

        if self.__attr['display-name'] != object_type.get_display_name():
            raise Exception('Attempt to update object type "%s", but display names do not match' % self.__attr['name'],
                            (self.__attr['display-name'], object_type.get_name()))

        if self.__attr['description'] != object_type.get_description():
            raise Exception('Attempt to update object type "%s", but descriptions do not match.' % self.__attr['name'],
                            (self.__attr['description'], object_type.get_name()))

        if self.__attr['data-type'] != str(object_type.get_data_type()):
            raise Exception('Attempt to update object type "%s", but data types do not match.' % self.__attr['name'],
                            (self.__attr['data-type'], object_type.get_name()))

        if self.__attr['compress'] != object_type.is_compressible():
            raise Exception(
                'Attempt to update object type "%s", but compress flags do not match.' % self.__attr['name'],
                (self.__attr['compress'], object_type.get_name()))

        if self.__attr['fuzzy-matching'] != object_type.get_fuzzy_matching():
            raise Exception('Attempt to update object type "%s", but fuzzy '
                            'matching attributes do not match.' % self.__attr['name'],
                            (self.__attr['fuzzy-matching'], object_type.get_name()))

        if self.__attr['regexp'] != object_type.get_regexp():
            raise Exception('Attempt to update object type "%s", but their '
                            'regular expressions do not match.' % self.__attr['name'],
                            (self.__attr['regexp'], object_type.get_name()))

        if self.__attr['version'] != object_type.get_version():
            raise Exception('Attempt to update object type "%s", but versions do not match.' % self.__attr['name'])

        self.validate()

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <objecttype> tag for this object type.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['compress'] = 'true' if self.__attr['compress'] else 'false'
        attribs['version'] = unicode(attribs['version'])

        return etree.Element('objecttype', attribs)
