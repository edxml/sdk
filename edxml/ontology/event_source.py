# -*- coding: utf-8 -*-

import re

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError


class EventSource(object):
    """
    Class representing an EDXML event source
    """

    SOURCE_URI_PATTERN = re.compile('^(/[a-z0-9-]+)*/$')
    ACQUISITION_DATE_PATTERN = re.compile('^[0-9]{8}$')

    def __init__(self, ontology, uri, description='no description available', acquisition_date='00000000'):

        self._attr = {
            'uri': str(uri).rstrip('/') + '/',
            'description': str(description),
            'date-acquired': str(acquisition_date)
        }

        self._ontology = ontology  # type: edxml.ontology.Ontology

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

    def get_acquisition_date_string(self):
        """

        Returns the acquisition date

        Returns:
          str: The date in yyyymmdd format
        """

        return self._attr['date-acquired']

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

    def validate(self):
        """

        Checks if the event source definition is valid.

        Raises:
          EDXMLValidationError
        Returns:
          edxml.ontology.EventSource: The EventSource instance

        """
        if not re.match(self.SOURCE_URI_PATTERN, self._attr['uri']):
            raise EDXMLValidationError(
                'Event source has an invalid URI: "%s"' % self._attr['uri']
            )

        if not 1 <= len(self._attr['description']) <= 128:
            raise EDXMLValidationError(
                'Event source has a description that is either empty or too long.')

        if not re.match(self.ACQUISITION_DATE_PATTERN, self._attr['date-acquired']):
            raise EDXMLValidationError(
                'Event source has an invalid acquisition date: "%s"' % self._attr['date-acquired']
            )

        return self

    @classmethod
    def create_from_xml(cls, source_element, ontology):
        return cls(
            ontology,
            source_element.attrib['uri'],
            source_element.attrib['description'],
            source_element.attrib['date-acquired']
        )

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
        if self._attr['uri'] != source.get_uri():
            raise Exception('Attempt to update event source "%s" with source "%s".' %
                            (self._attr['uri'], source.get_uri()))

        self.validate()

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <source> tag for this event source.

        Returns:
          etree.Element: The element

        """

        return etree.Element('source', self._attr)
