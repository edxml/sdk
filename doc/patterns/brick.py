# -*- coding: utf-8 -*-
import edxml


class ExampleBrick(edxml.ontology.Brick):
  """
  Example brick that defines one concept.
  """

  CONCEPT_COMPUTER = 'computer'

  @classmethod
  def generateConcepts(cls, targetOntology):
    yield targetOntology.CreateConcept('computer')\
                        .SetDescription('some kind of a computing device')\
                        .SetDisplayName('computer')

edxml.ontology.Ontology.RegisterBrick(ExampleBrick)
