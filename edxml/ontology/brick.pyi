# -*- coding: utf-8 -*-

import edxml
from typing import List


class Brick(object):

    @classmethod
    def generateObjectTypes(cls, targetOntology: edxml.ontology.Ontology) -> List[edxml.ontology.ObjectType]: ...

    def generateConcepts(cls, targetOntology: edxml.ontology.Ontology) -> List[edxml.ontology.Concept]: ...
