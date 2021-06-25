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
from datetime import datetime

from lxml import etree

import edxml.ontology

from edxml.error import EDXMLOntologyValidationError
from edxml.ontology import VersionedOntologyElement
from edxml.ontology.ontology_element import ontology_element_upgrade_error


class EventSource(VersionedOntologyElement):
    """
    Class representing an EDXML event source
    """

    SOURCE_URI_PATTERN = re.compile('^(/[a-z0-9-]+)*/$')
    ACQUISITION_DATE_PATTERN = re.compile('^[0-9]{8}$')

    def __init__(self, ontology, uri, description='no description available', acquisition_date=None):

        self._attr = {
            'uri': uri,
            'description': str(description),
            'date-acquired': acquisition_date,
            'version': 1
        }

        self._ontology = ontology  # type: edxml.ontology.Ontology

    def __repr__(self):
        return self._attr['uri']

    def __str__(self):
        return self._attr['uri']

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self._ontology._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._child_modified_callback()

    def get_uri(self):
        """

        Returns the source URI

        Returns:
          str:
        """
        return self._attr['uri']

    def get_description(self):
        """

        Returns the source description

        Returns:
          str:
        """
        return self._attr['description']

    def get_acquisition_date(self):
        """

        Returns the acquisition date as a datetime object or None
        in case no acquisition date is set.

        Returns:
          Optional[datetime.datetime]: The date
        """

        return datetime.strptime(self._attr['date-acquired'], '%Y%m%d') if self._attr['date-acquired'] else None

    def get_acquisition_date_string(self):
        """

        Returns the acquisition date as a string of None in case
        not acquisition date is set.

        Returns:
          Optional[str]: The date in yyyymmdd format
        """

        return self._attr['date-acquired']

    def get_version(self):
        """

        Returns the version of the source definition.

        Returns:
          int:
        """

        return self._attr['version']

    def set_description(self, description):
        """

        Sets the source description

        Args:
          description (str): Description

        Returns:
          edxml.ontology.EventSource: The EventSource instance
        """

        self._set_attr('description', str(description))
        return self

    def set_acquisition_date(self, date_time):
        """

        Sets the acquisition date

        Args:
          date_time (datetime.datetime): Acquisition date

        Returns:
          edxml.ontology.EventSource: The EventSource instance
        """

        self._set_attr('date-acquired', date_time.strftime('%Y%m01'))
        return self

    def set_acquisition_date_string(self, date_time):
        """

        Sets the acquisition date from a string value

        Args:
          date_time (str): The date in yyyymmdd format

        Returns:
          edxml.ontology.EventSource: The EventSource instance
        """

        self._set_attr('date-acquired', date_time)
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

    def validate(self):
        """

        Checks if the event source definition is valid.

        Raises:
          EDXMLOntologyValidationError
        Returns:
          edxml.ontology.EventSource: The EventSource instance

        """
        if not re.match(self.SOURCE_URI_PATTERN, self._attr['uri']):
            raise EDXMLOntologyValidationError(
                'Event source has an invalid URI: "%s"' % self._attr['uri']
            )

        if self._attr['description'] == '':
            raise EDXMLOntologyValidationError(
                'Event source %s has an empty description.' % self._attr['uri'])

        if len(self._attr['description']) > 128:
            raise EDXMLOntologyValidationError(
                'Event source %s has a description that is too long: "%s"' %
                (self._attr['uri'], self._attr['description']))

        if self._attr['date-acquired'] is not None:
            if not re.match(self.ACQUISITION_DATE_PATTERN, self._attr['date-acquired']):
                raise EDXMLOntologyValidationError(
                    'Event source has an invalid acquisition date: "%s"' % self._attr['date-acquired']
                )

        return self

    @classmethod
    def create_from_xml(cls, source_element, ontology):
        try:
            return cls(
                ontology,
                source_element.attrib['uri'],
                source_element.attrib['description'],
                source_element.attrib.get('date-acquired')
            ).set_version(source_element.attrib['version'])
        except KeyError as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate an event source from the following definition:\n" +
                etree.tostring(source_element, pretty_print=True, encoding='unicode') +
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

        if old.get_uri() != new.get_uri():
            raise ValueError("Sources with different URIs are not comparable.")

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['description', 'date-acquired']:
            equal &= old._attr[attr] == new._attr[attr]

        if equal:
            return 0

        if versions_differ:
            return -1 if other_is_newer else 1

        ontology_element_upgrade_error('event source', old, new)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, source):
        """

        Updates the event source to match the EventSource
        instance passed to this method, returning the
        updated instance.

        Args:
          source (edxml.ontology.EventSource): The new EventSource instance

        Returns:
          edxml.ontology.EventSource: The updated EventSource instance

        """
        if source > self:
            # The new definition is indeed newer. Update self.
            self.set_acquisition_date_string(source.get_acquisition_date_string())
            self.set_description(source.get_description())
            self.set_version(source.get_version())

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <source> tag for this event source.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self._attr)
        attribs['version'] = str(attribs['version'])

        if attribs['date-acquired'] is None:
            del attribs['date-acquired']

        return etree.Element('source', attribs)
