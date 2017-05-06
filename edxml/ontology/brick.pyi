# -*- coding: utf-8 -*-
from typing import List

import edxml


class Brick(object):

  @classmethod
  def generateObjectTypes(cls, targetOntology: edxml.ontology.Ontology) -> List[edxml.ontology.ObjectType]: ...
  def generateConcepts(cls, targetOntology: edxml.ontology.Ontology) -> List[edxml.ontology.Concept]: ...
