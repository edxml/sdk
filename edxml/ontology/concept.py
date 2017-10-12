# -*- coding: utf-8 -*-
from copy import deepcopy
from lxml import etree

import re
import sre_constants

import edxml
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import DataType


class Concept(object):
  """
  Class representing an EDXML concept
  """

  NAME_PATTERN = re.compile('^[a-z0-9.]{1,64}$')
  DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")

  def __init__(self, Ontology, Name, DisplayName = None, Description = None):

    self._attr = {
      'name':            Name,
      'display-name'   : DisplayName or ' '.join(('%s/%s' % (Name, Name)).split('.')),
      'description'    : Description or Name
    }

    self._ontology = Ontology  # type: edxml.ontology.Ontology

  def _childModifiedCallback(self):
    """Callback for change tracking"""
    return self

  def GetName(self):
    """

    Returns the name of the concept.

    Returns:
      str: The concept name
    """

    return self._attr['name']

  def GetDisplayName(self):
    """

    Returns the display-name attribute of the concept.

    Returns:
      str:
    """

    return self._attr['display-name']

  def GetDisplayNameSingular(self):
    """

    Returns the display name of the concept, in singular form.

    Returns:
      str:
    """

    return self._attr['display-name'].split('/')[0]

  def GetDisplayNamePlural(self):
    """

    Returns the display name of the concept, in plural form.

    Returns:
      str:
    """

    return self._attr['display-name'].split('/')[1]

  def GetDescription(self):
    """

    Returns the description of the concept.

    Returns:
      str:
    """

    return self._attr['description']

  def SetDescription(self, Description):
    """

    Sets the concept description

    Args:
      Description (str): Description

    Returns:
      edxml.ontology.Concept: The Concept instance
    """

    self._attr['description'] = str(Description)
    return self

  def SetDisplayName(self, Singular, Plural = None):
    """

    Configure the display name. If the plural form
    is omitted, it will be auto-generated by
    appending an 's' to the singular form.

    Args:
      Singular (str): display name (singular form)
      Plural (str): display name (plural form)

    Returns:
      edxml.ontology.Concept: The Concept instance
    """

    if Plural is None:
      Plural = '%ss' % Singular
    self._attr['display-name'] = '%s/%s' % (Singular, Plural)

    return self

  def Validate(self):
    """

    Checks if the concept is valid. It only looks
    at the attributes of the definition itself. Since it does
    not have access to the full ontology, the context of
    the ontology is not considered. For example, it does not
    check if other, conflicting concept definitions exist.

    Raises:
      EDXMLValidationError

    Returns:
      edxml.ontology.Concept: The Concept instance

    """
    if not len(self._attr['name']) <= 64:
      raise EDXMLValidationError('The name of concept "%s" is too long.' % self._attr['name'])
    if not re.match(self.NAME_PATTERN, self._attr['name']):
      raise EDXMLValidationError('Concept "%s" has an invalid name.' % self._attr['name'])

    if not len(self._attr['display-name']) <= 64:
      raise EDXMLValidationError(
        'The display name of concept "%s" is too long: "%s".' % (self._attr['name'], self._attr['display-name'])
      )
    if not re.match(self.DISPLAY_NAME_PATTERN, self._attr['display-name']):
      raise EDXMLValidationError(
        'Concept "%s" has an invalid display name: "%s"' % (self._attr['name'], self._attr['display-name'])
      )

    if not len(self._attr['description']) <= 128:
      raise EDXMLValidationError(
        'The description of concept "%s" is too long: "%s"' % (self._attr['name'], self._attr['description'])
      )

    return self

  @classmethod
  def Read(cls, typeElement, ontology):
    return cls(
      ontology,
      typeElement.attrib['name'],
      typeElement.attrib['display-name'],
      typeElement.attrib['description'],
    )

  def Update(self, concept):
    """

    Args:
      concept (edxml.ontology.Concept): The new Concept instance

    Returns:
      edxml.ontology.Concept: The updated Concept instance

    """
    if self._attr['name'] != concept.GetName():
      raise Exception('Attempt to update concept "%s" with concept "%s".' %
                      (self._attr['name'], concept.GetName()))

    if self._attr['display-name'] != concept.GetDisplayName():
      raise Exception('Attempt to update concept "%s", but display names do not match.' % self._attr['name'],
                      (self._attr['display-name'], concept.GetName()))

    if self._attr['description'] != concept.GetDescription():
      raise Exception('Attempt to update concept "%s", but descriptions do not match.' % self._attr['name'],
                      (self._attr['description'], concept.GetName()))

    self.Validate()

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <concept> tag for this concept.

    Returns:
      etree.Element: The element

    """

    return etree.Element('concept', self._attr)
