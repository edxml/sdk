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

import copy
import re
import sre_constants

from lxml import etree

import edxml.ontology

from edxml.error import EDXMLEventValidationError, EDXMLOntologyValidationError

from .data_type import DataType
from .ontology_element import VersionedOntologyElement, ontology_element_upgrade_error
from .util import normalize_xml_token


class ObjectType(VersionedOntologyElement):
    """
    Class representing an EDXML object type
    """

    NAME_PATTERN = re.compile('^[a-z0-9.-]{1,64}$')
    DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
    FUZZY_MATCHING_PATTERN = re.compile(
        r"^|(phonetic)|(substring:.*)|(\[[0-9]{1,2}:\])|(\[:[0-9]{1,2}\])$")

    def __init__(self, ontology, name, display_name_singular=None, display_name_plural=None, description=None,
                 data_type='string:0:mc:u', unit_name=None, unit_symbol=None, prefix_radix=None, compress=False,
                 xref=None, fuzzy_matching=None, regex_hard=None, regex_soft=None):

        display_name_singular = display_name_singular or name.replace('.', ' ')
        display_name_plural = display_name_plural or display_name_singular + 's'

        self.__attr = {
            'name': name,
            'display-name-singular': display_name_singular,
            'display-name-plural': display_name_plural,
            'description': description or name,
            'data-type': data_type,
            'unit-name': unit_name,
            'unit-symbol': unit_symbol,
            'prefix-radix': prefix_radix,
            'xref': xref,
            'compress': bool(compress),
            'fuzzy-matching': fuzzy_matching,
            'regex-hard': regex_hard,
            'regex-soft': regex_soft,
            'version': 1
        }

        self.__ontology = ontology  # type: edxml.ontology.Ontology

        self.__versions = {1: copy.copy(self)}

    def __copy__(self):
        new = self.__new__(ObjectType)
        new.__attr = self.__attr.copy()
        return new

    def __repr__(self):
        return f"{self.__attr['name']} ({self.__attr['data-type']}))"

    def __str__(self):
        return self.__attr['name']

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

    def get_display_name_singular(self):
        """

        Returns the display name of the object type, in singular form.

        Returns:
          str:
        """

        return self.__attr['display-name-singular']

    def get_display_name_plural(self):
        """

        Returns the display name of the object type, in plural form.

        Returns:
          str:
        """

        return self.__attr['display-name-plural']

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

    def get_unit_name(self):
        """

        Returns the name of the measurement unit or None in case
        the object type does not have any associated unit.

        Returns:
          Optional[str]: unit name
        """

        return self.__attr['unit-name']

    def get_unit_symbol(self):
        """

        Returns the symbol of the measurement unit or None in case
        the object type does not have any associated unit.

        Returns:
          Optional[str]: unit symbol
        """

        return self.__attr['unit-symbol']

    def get_prefix_radix(self):
        """

        Returns the natural radix that should be used for
        metric prefixes of numerical object types.

        Returns:
          Optional[int]: radix
        """

        return self.__attr['prefix-radix'] or 10

    def is_compressible(self):
        """

        Returns True if compression is advised for the object type,
        returns False otherwise.

        Returns:
          bool:
        """

        return self.__attr['compress']

    def get_xref(self):
        """

        Returns the external reference to additional information
        about the object type or None in case it does not define any.

        Returns:
          Optional[str]: xref
        """

        return self.__attr['xref']

    def get_fuzzy_matching(self):
        """

        Returns the EDXML fuzzy-matching attribute for the object type or
        None in case it does not define any.

        Returns:
          Optional[str]:
        """

        return self.__attr['fuzzy-matching']

    def get_regex_hard(self):
        """

        Returns the regular expression that object values must match.
        Returns None in case no hard regular expression is associated
        with the object type.

        Note that the regular expression is not anchored to the start
        and end of the object value string even though object values
        must fully matches the expression from start to end. Be sure
        to wrap the expression in anchors where full string matching
        is needed.

        Returns:
          Optional[str]:
        """

        return self.__attr['regex-hard']

    def get_regex_soft(self):
        """

        Returns the regular expression that can be used to identify
        valid object values or generate synthetic values. Returns None
        in case no soft regular expression is associated with the
        object type.

        Note that the regular expression is not anchored to the start
        and end of the object value string even though the expression
        should match full object values from start to end. Be sure
        to wrap the expression in anchors before use.

        Returns:
          Optional[str]:
        """

        return self.__attr['regex-soft']

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

    def set_unit(self, unit_name, unit_symbol):
        """

        Configure the measurement unit name and symbol.

        Args:
          unit_name (str): Unit name
          unit_symbol (str): Unit symbol

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('unit-name', unit_name)
        self._set_attr('unit-symbol', unit_symbol)
        return self

    def set_prefix_radix(self, radix):
        """

        Configure the natural radix that should be used for
        metric prefixes of numerical object types

        Args:
          radix (int): Radix

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('prefix-radix', radix)
        return self

    def set_xref(self, url):
        """

        Configure the URL pointing to additional information
        about the object type.

        Args:
          url (int): URL

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('xref', url)
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

        self._set_attr('display-name-singular', singular)
        self._set_attr('display-name-plural', plural or (singular + 's'))
        return self

    def set_regex_hard(self, pattern):
        """

        Configure a regular expression that object
        values must match.

        Args:
          pattern (str): Regular expression

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('regex-hard', pattern)
        return self

    def set_regex_soft(self, pattern):
        """

        Configure a regular expression that should match
        values that are valid for the object type.

        Args:
          pattern (str): Regular expression

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        self._set_attr('regex-soft', pattern)
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

        Sets the object type version

        Args:
          version (int): Version

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """

        self.__versions[self.__attr['version']] = copy.copy(self)
        self._set_attr('version', int(version))
        return self

    def upgrade(self):
        """
        Verifies if the current instance is a valid upgrade of the instance as it
        was when the version was last changed. When successful the version number is
        incremented.

        This method is used for fluent upgrading of ontology bricks, allowing
        definitions of object types to be changed in a single call chain while
        making sure that no backward incompatible changes are made.

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        new_version = copy.copy(self)
        new_version.__attr['version'] = self.__attr['version'] + 1
        if new_version > self.__versions[self.__attr['version']]:
            self.set_version(self.__attr['version'] + 1)
        else:
            raise Exception(
                'Cannot upgrade object type. '
                'Apparently no changes were made since the last time the version number changed.'
            )

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

        return DataType(self.__attr['data-type']).generate_relaxng(self.__attr['regex-hard'])

    def validate_object_value(self, value):
        """

        Validates the provided object value against
        the object type definition as well as its
        data type, raising an EDXMLValidationException
        when the value is invalid.

        Args:
          value (str): Object value

        Raises:
          EDXMLEventValidationError

        Returns:
           edxml.ontology.ObjectType: The ObjectType instance
        """

        # First, validate against data type
        self.get_data_type().validate_object_value(value)

        # Validate against object type specific restrictions,
        # like the regular expression.
        split_data_type = self.__attr['data-type'].split(':')

        if split_data_type[0] == 'string':
            if self.__attr['regex-hard'] is not None and not re.match('^%s$' % self.__attr['regex-hard'], value):
                raise EDXMLEventValidationError(
                    "Object value '%s' of object type %s does not match hard regex '%s' of the object type."
                    % (value, self.__attr['name'], self.__attr['regex-hard'])
                )

    def validate(self):
        """

        Checks if the object type is valid. It only looks
        at the attributes of the definition itself. Since it does
        not have access to the full ontology, the context of
        the event type is not considered. For example, it does not
        check if other, conflicting object type definitions exist.

        Raises:
          EDXMLOntologyValidationError

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance

        """
        if not len(self.__attr['name']) <= 64:
            raise EDXMLOntologyValidationError(
                'The name of object type "%s" is too long.' % self.__attr['name'])
        if not re.match(self.NAME_PATTERN, self.__attr['name']):
            raise EDXMLOntologyValidationError(
                'Object type "%s" has an invalid name.' % self.__attr['name'])

        if not len(self.__attr['display-name-singular']) <= 32:
            raise EDXMLOntologyValidationError(
                'The singular display name of object type "%s" is too long: "%s".' % (
                    self.__attr['name'], self.__attr['display-name-singular'])
            )

        if not len(self.__attr['display-name-plural']) <= 32:
            raise EDXMLOntologyValidationError(
                'The plural display name of object type "%s" is too long: "%s".' % (
                    self.__attr['name'], self.__attr['display-name-plural'])
            )

        if self.__attr['unit-name'] is not None and len(self.__attr['unit-name']) > 32:
            raise EDXMLOntologyValidationError(
                'The unit name of object type "%s" is too long: "%s".' % (
                    self.__attr['name'], self.__attr['unit-name'])
            )

        if self.__attr['unit-symbol'] is not None and len(self.__attr['unit-symbol']) > 32:
            raise EDXMLOntologyValidationError(
                'The unit symbol of object type "%s" is too long: "%s".' % (
                    self.__attr['name'], self.__attr['unit-symbol'])
            )

        token_attributes = ('display-name-singular', 'display-name-plural', 'description', 'unit-name', 'unit-symbol')

        for token_attribute in token_attributes:
            if normalize_xml_token(self.__attr[token_attribute] or '') != (self.__attr[token_attribute] or ''):
                raise EDXMLOntologyValidationError(
                    'The %s attribute of object type "%s" contains illegal whitespace characters: "%s"' %
                    (token_attribute, self.__attr['name'], self.__attr[token_attribute])
                )

        if not len(self.__attr['description']) <= 128:
            raise EDXMLOntologyValidationError(
                'The description of object type "%s" is too long: "%s"' % (
                    self.__attr['name'], self.__attr['description'])
            )

        if self.__attr['prefix-radix'] not in (None, 2, 10, 60):
            raise EDXMLOntologyValidationError(
                'The prefix radix of object type "%s" must be 2, 10 or 60, %s is not a valid value.' % (
                    self.__attr['name'], self.__attr['prefix-radix'])
            )

        if self.__attr['fuzzy-matching'] is not None:
            if self.get_data_type().get_family() != 'string':
                raise EDXMLOntologyValidationError(
                    'Object type "%s" specifies a fuzzy matching method while it does not have a string data type.' %
                    self.__attr['name']
                )
            if not re.match(self.FUZZY_MATCHING_PATTERN, self.__attr['fuzzy-matching']):
                raise EDXMLOntologyValidationError(
                    'Object type "%s" has an invalid fuzzy-matching attribute: "%s"' %
                    (self.__attr['name'], self.__attr['fuzzy-matching'])
                )
            if self.__attr['fuzzy-matching'][:10] == 'substring:':
                try:
                    re.compile('%s' % self.__attr['fuzzy-matching'][10:])
                except sre_constants.error:
                    raise EDXMLOntologyValidationError(
                        'Definition of object type %s has an invalid regular expression in its '
                        'fuzzy-matching attribute: "%s"' %
                        (self.__attr['name'], self.__attr['fuzzy-matching']))

        if type(self.__attr['compress']) != bool:
            raise EDXMLOntologyValidationError(
                'Object type "%s" has an invalid compress attribute: "%s"' % (
                    self.__attr['name'], repr(self.__attr['compress']))
            )

        for soft_hard in ['soft', 'hard']:
            if self.__attr['regex-' + soft_hard] is not None:
                if self.get_data_type().get_family() != 'string':
                    raise EDXMLOntologyValidationError(
                        'Object type "%s" has a %s regular expression while its data type is not a string.' %
                        (self.__attr['name'], soft_hard)
                    )
                try:
                    re.compile(self.__attr['regex-' + soft_hard])
                except sre_constants.error:
                    raise EDXMLOntologyValidationError(
                        'Object type "%s" contains invalid %s regular expression: "%s"' %
                        (self.__attr['name'], soft_hard, self.__attr['regex-hard'])
                    )

        if self.__attr['unit-name'] is None and self.__attr['unit-symbol'] is not None:
            raise EDXMLOntologyValidationError(
                'Object type "%s" contains a unit symbol without a unit name.' % self.__attr['name']
            )

        if self.__attr['unit-symbol'] is None and self.__attr['unit-name'] is not None:
            raise EDXMLOntologyValidationError(
                'Object type "%s" contains a unit name without a unit symbol.' % self.__attr['name']
            )

        if self.__attr['unit-name'] is not None and self.get_data_type().get_family() != 'number':
            raise EDXMLOntologyValidationError(
                'Object type "%s" specifies a unit name while it is not numeric.' % self.__attr['name']
            )

        if self.__attr['prefix-radix'] is not None and self.__attr['unit-name'] is None:
            raise EDXMLOntologyValidationError(
                'Object type "%s" specifies a prefix radix while not specifying a unit.' % self.__attr['name']
            )

        DataType(self.__attr['data-type']).validate()

        return self

    @classmethod
    def create_from_xml(cls, type_element, ontology):
        try:
            return cls(
                ontology,
                type_element.attrib['name'],
                type_element.attrib['display-name-singular'],
                type_element.attrib['display-name-plural'],
                type_element.attrib['description'],
                type_element.attrib['data-type'],
                type_element.get('unit-name'),
                type_element.get('unit-symbol'),
                type_element.get('prefix-radix'),
                type_element.get('compress', 'false') == 'true',
                type_element.get('xref'),
                type_element.get('fuzzy-matching'),
                type_element.get('regex-hard'),
                type_element.get('regex-soft')
            ).set_version(type_element.attrib['version'])
        except KeyError as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate an object type from the following definition:\n" +
                etree.tostring(type_element, pretty_print=True, encoding='unicode') +
                "\nMissing attribute: " + str(e)
            )

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
            raise ValueError("Object types with different names are not comparable.")

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['display-name-singular', 'display-name-plural', 'description', 'compress', 'fuzzy-matching',
                     'xref', 'unit-name', 'unit-symbol', 'prefix-radix', 'regex-soft']:
            equal &= old.__attr[attr] == new.__attr[attr]

        # Check for illegal upgrade paths:

        if old.get_regex_hard() != new.get_regex_hard():
            equal = False
            if old.get_regex_hard() is None or \
                    (new.get_regex_hard() is not None and new.get_regex_hard().find(old.get_regex_hard() + "|") != 0):
                # The new expression is not a valid extension of the old one.
                is_valid_upgrade = False

        if old.get_data_type().get() != new.get_data_type().get():
            # The data types differ
            equal = False
            if not new.get_data_type().is_valid_upgrade_of(old.get_data_type()):
                # Data type cannot be upgraded like this.
                is_valid_upgrade = False

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        ontology_element_upgrade_error('object type', old, new)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, object_type):
        """

        Args:
          object_type (edxml.ontology.ObjectType): The new ObjectType instance

        Returns:
          edxml.ontology.ObjectType: The updated ObjectType instance

        """
        if object_type > self:
            # The new definition is indeed newer. Update self.
            self.set_display_name(object_type.get_display_name_singular(), object_type.get_display_name_plural())
            self.set_description(object_type.get_description())
            self.compress(object_type.is_compressible())
            self.set_xref(object_type.get_xref())
            self.set_unit(object_type.get_unit_name(), object_type.get_unit_symbol())
            self.set_prefix_radix(object_type.__attr['prefix-radix'])
            self.set_regex_hard(object_type.get_regex_hard())
            self.set_regex_soft(object_type.get_regex_soft())
            self.set_fuzzy_matching_attribute(object_type.get_fuzzy_matching())
            self.set_version(object_type.get_version())
            self.set_data_type(object_type.get_data_type())

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <object-type> tag for this object type.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['compress'] = 'true' if self.__attr['compress'] else 'false'
        attribs['version'] = str(attribs['version'])

        if attribs['compress'] == 'false':
            del attribs['compress']

        if attribs['xref'] is None:
            del attribs['xref']

        if attribs['regex-hard'] is None:
            del attribs['regex-hard']

        if attribs['regex-soft'] is None:
            del attribs['regex-soft']

        if attribs['fuzzy-matching'] is None:
            del attribs['fuzzy-matching']

        if attribs['prefix-radix'] in (None, 10):
            del attribs['prefix-radix']
        else:
            attribs['prefix-radix'] = str(attribs['prefix-radix'])

        if attribs['unit-name'] is None or attribs['unit-symbol'] is None:
            del attribs['unit-name']
            del attribs['unit-symbol']

        return etree.Element('object-type', attribs)
