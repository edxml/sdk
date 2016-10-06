# -*- coding: utf-8 -*-

from edxml.EDXMLWriter import EDXMLWriter

class PropertyRelation(object):
  """
  Class representing a relation between two EDXML properties
  """

  def __init__(self, Source, Dest, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):

    self._attr = {
      'property1':         Source,
      'property2':         Dest,
      'description':       Description,
      'type':              '%s:%s' % (TypeClass, TypePredicate),
      'confidence':        float(Confidence),
      'directed':          bool(Directed),
    }

  @classmethod
  def Create(cls, Source, Dest, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):
    """

    Create a new property relation

    Args:
      Source (str): Name of source property
      Dest (str): Name of destination property
      Description (str): Relation description, with property placeholders
      TypeClass (str): Relation type class ('inter', 'intra' or 'other')
      TypePredicate (str): free form predicate
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      PropertyRelation:
    """
    return cls(Source, Dest, Description, TypeClass, TypePredicate, Confidence, Directed)

  def GetSource(self):
    """

    Returns the name of the source property.

    Returns:
      str:
    """
    return self._attr['property1']

  def GetDest(self):
    """

    Returns the name of the destination property.

    Returns:
      str:
    """
    return self._attr['property1']

  def GetDescription(self):
    """

    Returns the relation description.

    Returns:
      str:
    """
    return self._attr['description']

  def GetType(self):
    """

    Returns the relation type.

    Returns:
      str:
    """
    return self._attr['type']

  def GetTypeClass(self):
    """

    Returns the class part of the relation type.

    Returns:
      str:
    """
    return self._attr['type'].split(':')[0]

  def GetTypePredicate(self):
    """

    Returns the predicate part of the relation type.

    Returns:
      str:
    """
    return self._attr['type'].split(':')[1]

  def GetConfidence(self):
    """

    Returns the relation confidence.

    Returns:
      float:
    """
    return self._attr['confidence']

  def IsDirected(self):
    """

    Returns True when the relation is directed,
    returns False otherwise.

    Returns:
      bool:
    """
    return self._attr['directed']

  def SetConfidence(self, Confidence):
    """

    Configure the relation confidence

    Args:
     Confidence (float): Relation confidence [0.0,1.0]

    Returns:
      PropertyRelation: The PropertyRelation instance
    """

    self._attr['confidence'] = float(Confidence)
    return self

  def Directed(self):
    """

    Marks the property relation as directed

    Returns:
      PropertyRelation: The PropertyRelation instance
    """
    self._attr['directed'] = True
    return self

  def Undirected(self):
    """

    Marks the property relation as undirected

    Returns:
      PropertyRelation: The PropertyRelation instance
    """
    self._attr['directed'] = False
    return self

  def Write(self, Writer):
    """

    Writes the property relation into the provided
    EDXMLWriter instance

    Args:
      Writer (EDXMLWriter): EDXMLWriter instance

    Returns:
      PropertyRelation: The PropertyRelation instance
    """

    Writer.AddRelation(self._attr['property1'], self._attr['property2'], self._attr['type'], self._attr['description'], self._attr['confidence'], self._attr['directed'])

    return self
