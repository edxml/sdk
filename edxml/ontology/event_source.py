# -*- coding: utf-8 -*-
from lxml import etree

import re
import uuid
from time import strftime, gmtime

import edxml
from edxml.EDXMLBase import EDXMLValidationError


class EventSource(object):
  """
  Class representing an EDXML event source
  """

  SOURCE_URL_PATTERN = re.compile('^(/[a-z0-9-]+)*/$')
  ACQUISITION_DATE_PATTERN = re.compile('^[0-9]{8}$')

  def __init__(self, Ontology, Id, Url, Description = None, AcquisitionDate = None):

    self._attr = {
      'source-id':     str(Id),
      'url':           str(Url).rstrip('/') + '/',
      'description':   str(Description) if Description else 'undescribed source',
      'date-acquired': str(AcquisitionDate) if AcquisitionDate else strftime("%Y%m%d", gmtime())
    }

    self._ontology = Ontology  # type: edxml.ontology.Ontology

  def _setOntology(self, ontology):
    self._ontology = ontology
    return self


  def GetId(self):
    """

    Returns the source Id

    Returns:
      str:
    """
    return self._attr['source-id']

  def GetUrl(self):
    """

    Returns the source URL

    Returns:
      str:
    """
    return self._attr['url']

  def GetAcquisitionDateString(self):
    """

    Returns the acquisition date

    Returns:
      str: The date in yyyymmdd format
    """

    return self._attr['date-acquired']

  def SetDescription(self, Description):
    """

    Sets the source description

    Args:
      Description (str): Description

    Returns:
      EventSource: The EventSource instance
    """

    self._attr['description'] = str(Description)
    return self

  def Validate(self):
    """

    Checks if the event source definition is valid.

    Raises:
      EDXMLValidationError
    Returns:
      EventSource: The EventSource instance

    """
    if len(self._attr['source-id']) == 0:
      raise EDXMLValidationError('Event source has an empty source-id attribute.')

    if not re.match(self.SOURCE_URL_PATTERN, self._attr['url']):
      raise EDXMLValidationError(
        'Event source has an invalid URL: "%s"' % self._attr['url']
      )

    if not 1 <= len(self._attr['description']) <= 128:
      raise EDXMLValidationError('Event source has a description that is either empty or too long.')

    if not re.match(self.ACQUISITION_DATE_PATTERN, self._attr['date-acquired']):
      raise EDXMLValidationError(
        'Event source has an invalid acquisition date: "%s"' % self._attr['date-acquired']
      )

    return self

  @classmethod
  def Read(cls, sourceElement, ontology):
    return cls(
      ontology,
      sourceElement.attrib['source-id'],
      sourceElement.attrib['url'],
      sourceElement.attrib['description'],
      sourceElement.attrib['date-acquired']
    )

  def Update(self, source):
    """

    Updates the event source to match the EventSource
    instance passed to this method, returning the
    updated instance.

    Args:
      source (EventSource): The new EventSource instance

    Returns:
      EventSource: The updated EventSource instance

    """
    if self._attr['url'] != source.GetUrl():
      raise Exception('Attempt to update event source "%s" with source "%s".',
                      (self._attr['url'], source.GetUrl()))

    self.Validate()

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <source> tag for this event source.

    Returns:
      etree.Element: The element

    """

    return etree.Element('source', self._attr)
