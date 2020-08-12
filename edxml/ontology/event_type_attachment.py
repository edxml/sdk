# -*- coding: utf-8 -*-

import re

from lxml import etree
import edxml
from edxml.error import EDXMLValidationError
from edxml.ontology import OntologyElement, normalize_xml_token


class EventTypeAttachment(OntologyElement):
    """
    Class representing an EDXML event attachment definition
    """

    NAME_PATTERN = re.compile("^[a-z0-9-]*$")
    DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")

    def __init__(self, event_type, name='default', media_type='text/plain', display_name_singular=None,
                 display_name_plural=None, description=None, encode_base64=False):
        """

        Creates a new event attachment definition.

        When no description is given, the name is used as description.
        When no singular display name is given, the name is used as singular display name.
        When no plural display name is given, it is constructed by appending an 's' to
        the singular form.

        Args:
            event_type (edxml.ontology.EventType): The event type containing the attachment definition
            name (str): Name of the attachment
            media_type (str): RFC 6838 media type
            display_name_singular (str): display name (singular)
            display_name_plural (str): display name (plural)
            description (str): Description (EDXML template)
            encode_base64 (bool): Encode as base64 string yes / no
        """

        display_name_singular = display_name_singular or name.replace('-', ' ')
        display_name_plural = display_name_plural or display_name_singular + 's'

        self._attr = {
            'name': name,
            'media-type': media_type,
            'display-name-singular': display_name_singular,
            'display-name-plural': display_name_plural,
            'description': description or display_name_singular,
            'encoding': 'base64' if encode_base64 else 'unicode'
        }

        self._event_type = event_type

    def __repr__(self):
        return f"{self._attr['name']} of event type {self._event_type.get_name()}"

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self._event_type._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._child_modified_callback()

    def set_description(self, description):
        """
        Sets the EDXML attachment description

        Args:
          description (str): description

        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """
        self._set_attr('description', description)

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
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """

        self._set_attr('display-name-singular', singular)
        self._set_attr('display-name-plural', plural or (singular + 's'))
        return self

    def set_media_type(self, media_type):
        """

        Configure the media type. This must be a valid RFC 6838 media type.

        Args:
          media_type (str): Media type

        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """

        self._set_attr('media-type', media_type)
        return self

    def set_encoding(self, encoding):
        """

        Sets the encoding to either 'unicode' or 'base64'.

        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """

        if encoding not in ('base64', 'unicode'):
            raise ValueError('Invalid attachment encoding: ' + encoding)

        self._set_attr('encoding', encoding)
        return self

    def set_encoding_unicode(self):
        """

        Sets the encoding to unicode, which means that the attachment must be a
        valid unicode string. This is the default encoding for attachments.

        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """

        self._set_attr('encoding', 'unicode')
        return self

    def set_encoding_base64(self):
        """

        Sets the encoding to base64, which means that the attachment must be a
        valid base64 encoding string.

        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance
        """

        self._set_attr('encoding', 'base64')
        return self

    def get_name(self):
        """

        Returns the attachment name

        Returns:
          str:
        """
        return self._attr['name']

    def get_description(self):
        """

        Returns the attachment description

        Returns:
          str:
        """
        return self._attr['description']

    def get_display_name_singular(self):
        """

        Returns the display name, in singular form.

        Returns:
          str:
        """
        return self._attr['display-name-singular']

    def get_display_name_plural(self):
        """

        Returns the display name, in plural form.

        Returns:
          str:
        """
        return self._attr['display-name-plural']

    def get_media_type(self):
        """

        Returns the media type.

        Returns:
          str:
        """
        return self._attr['media-type']

    def get_encoding(self):
        """

        Returns the encoding, either 'unicode' or 'base64'.

        Returns:
          str:
        """
        return self._attr['encoding']

    def is_unicode_string(self):
        """

        Returns True when the attachment is a unicode encoded string,
        returns False otherwise.

        Returns:
          bool:
        """
        return self._attr['encoding'] == 'unicode'

    def is_base64_string(self):
        """

        Returns True when the attachment is a base64 encoded string,
        returns False otherwise.

        Returns:
          bool:
        """
        return self._attr['encoding'] == 'base64'

    def validate(self):
        """

        Checks if the event type attachment is valid. It only looks
        at the attributes of the definition itself. For example, it
        does not check that the attachment has an id that is unique
        within the event type.

        Raises:
          EDXMLValidationError
        Returns:
          edxml.ontology.EventTypeAttachment: The EventTypeAttachment instance

        """

        if not 1 <= len(self._attr['name']) <= 64:
            raise EDXMLValidationError(
                'Event type "%s" has an invalid name.' % self._attr['name']
            )
        if not re.match(self.NAME_PATTERN, self._attr['name']):
            raise EDXMLValidationError(
                'Event type "%s" has an invalid name.' % self._attr['name']
            )

        if not 1 <= len(self._attr['description']) <= 128:
            raise EDXMLValidationError(
                'An attachment definition contains a description attribute that is either empty or too long: "%s"'
                % self._attr['description']
            )

        if normalize_xml_token(self._attr['description']) != self._attr['description']:
            raise EDXMLValidationError(
                'The description of attachment "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['description'])
            )

        if not len(self._attr['display-name-singular']) <= 32:
            raise EDXMLValidationError(
                'The singular display name of attachment "%s" is too long: "%s"' % (
                    self._attr['name'], self._attr['display-name-singular'])
            )

        if not len(self._attr['display-name-plural']) <= 32:
            raise EDXMLValidationError(
                'The plural display name of attachment "%s" is too long: "%s"' % (
                    self._attr['name'], self._attr['display-name-plural'])
            )

        if normalize_xml_token(self._attr['display-name-singular']) != self._attr['display-name-singular']:
            raise EDXMLValidationError(
                'The singular display name of attachment "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['display-name-singular'])
            )

        if normalize_xml_token(self._attr['display-name-plural']) != self._attr['display-name-plural']:
            raise EDXMLValidationError(
                'The plural display name of attachment "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['display-name-plural'])
            )

        try:
            edxml.Template(self._attr['description']).validate(self._event_type)
        except EDXMLValidationError as e:
            raise EDXMLValidationError(
                'The description template of attachment "%s" is invalid: "%s"\nThe validator said: %s' % (
                    self._attr['name'], self._attr['display-name-plural'], str(e))
            )

        return self

    @classmethod
    def create_from_xml(cls, element, event_type):
        try:
            return cls(
                event_type,
                element.attrib['name'],
                element.attrib['media-type'],
                element.attrib['display-name-singular'],
                element.attrib['display-name-plural'],
                element.attrib['description'],
                element.attrib['encoding'] == 'base64'
            )
        except KeyError as e:
            raise EDXMLValidationError(
                "Failed to instantiate an event attachment from the following definition:\n" +
                etree.tostring(element, pretty_print=True, encoding='unicode') +
                "\nError message: " + str(e)
            )

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        # Note that attachment definitions are part of event type definitions,
        # so we look at the version of the event type for which this attachment is defined.
        other_is_newer = other._event_type.get_version() > self._event_type.get_version()
        versions_differ = other._event_type.get_version() != self._event_type.get_version()

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
            raise ValueError("Attachments with different names are not comparable.")

        if old._event_type.get_name() != new._event_type.get_name():
            raise EDXMLValidationError(
                "Attempt to compare event type attachment definitions from two different event types"
            )

        # Check for illegal upgrade paths:

        if old.get_media_type() != new.get_media_type():
            # Media types differ, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_encoding() != new.get_encoding():
            # Content encoding differs, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        equal &= old.get_description() == new.get_description()
        equal &= old.get_display_name_singular() == new.get_display_name_singular()
        equal &= old.get_display_name_plural() == new.get_display_name_plural()

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        problem = 'invalid upgrades / downgrades of one another' if versions_differ else 'in conflict'

        old_version = str(old._event_type.get_version())
        new_version = str(new._event_type.get_version())

        if not versions_differ:
            new_version += ' (conflicting definition)'

        raise EDXMLValidationError(
            "Definitions of event type {} are {} due to the following difference in the definitions "
            "of their {} attachment:"
            "\nVersion {}:\n{}\nVersion {}:\n{}".format(
                self._event_type.get_name(),
                problem,
                self.get_name(),
                old_version,
                etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
                new_version,
                etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
            )
        )

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, attachment):
        """

        Updates the attachment to match the EventTypeAttachment
        instance passed to this method, returning the
        updated instance.

        Args:
          attachment (edxml.ontology.EventTypeAttachment): The new EventTypeAttachment instance

        Returns:
          edxml.ontology.EventTypeAttachment: The updated EventTypeAttachment instance

        """
        if attachment > self:
            # The new definition is indeed newer. Update self.
            self.set_description(attachment.get_description())
            self.set_display_name(attachment.get_display_name_singular(), attachment.get_display_name_plural())
            self._event_type = attachment._event_type

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <attachment> tag for this event type attachment.

        Returns:
          etree.Element: The element

        """

        return etree.Element('attachment', self._attr)
