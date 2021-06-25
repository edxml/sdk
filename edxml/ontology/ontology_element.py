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

from abc import abstractmethod, ABC
from functools import total_ordering
from lxml import etree

from edxml.error import EDXMLOntologyValidationError


def ontology_element_upgrade_error(element_name, old, new):
    """

    Raises a validation error for upgrades / downgrades / conflicts involving
    some ontology root element, like a concept or an object type.

    Args:
        element_name (str): Name of the type of ontology element
        old (VersionedOntologyElement): Old version
        new (VersionedOntologyElement): New version

    Raises:
        EDXMLOntologyValidationError
    """

    old_version = str(old.get_version())
    new_version = str(new.get_version())

    versions_differ = old_version != new_version

    problem = 'invalid upgrades / downgrades of one another' if versions_differ else 'in conflict'

    if not versions_differ:
        new_version += ' (conflicting definition)'

    raise EDXMLOntologyValidationError(
        "Definitions of a {} ({}) are {} due to the following difference in their definitions:\n"
        "Version {}:\n{}\nVersion {}:\n{}".format(
            element_name,
            str(old),
            problem,
            old_version,
            etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
            new_version,
            etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
        )
    )


def event_type_element_upgrade_error(element_name, old, new, old_type, new_type):
    """

    Raises a validation error for upgrades / downgrades / conflicts involving
    some element of an event type, like a property or an attachment.

    Args:
        element_name (str): Name of the type of ontology element
        old (OntologyElement): Old version
        new (OntologyElement): New version
        old_type (edxml.ontology.EventType): Old event type
        new_type (edxml.ontology.EventType): New event type

    Raises:
        EDXMLValidationError
    """

    old_version = str(old_type.get_version())
    new_version = str(new_type.get_version())

    versions_differ = old_version != new_version

    problem = 'invalid upgrades / downgrades of one another' if versions_differ else 'in conflict'

    if not versions_differ:
        new_version += ' (conflicting definition)'

    raise EDXMLOntologyValidationError(
        "Definitions of event type {} are {} due to the following difference in the definitions of a {} ({}):"
        "\nVersion {}:\n{}\nVersion {}:\n{}".format(
            old_type.get_name(),
            problem,
            str(old),
            element_name,
            old_version,
            etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
            new_version,
            etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
        )
    )


@total_ordering
class OntologyElement(ABC):
    """
    Class representing an EDXML ontology element
    """

    @abstractmethod
    def validate(self):
        raise NotImplementedError

    @abstractmethod
    def update(self, element):
        raise NotImplementedError

    @abstractmethod
    def __cmp__(self, other):
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError

    @abstractmethod
    def __ne__(self, other):
        raise NotImplementedError

    @abstractmethod
    def __lt__(self, other):
        raise NotImplementedError

    @abstractmethod
    def generate_xml(self):
        raise NotImplementedError


class VersionedOntologyElement(OntologyElement):
    """
    An ontology element that is versioned, such as an object type,
    concept, event type or an event source.
    """

    @abstractmethod
    def get_version(self):
        """

        Returns the version of the ontology element

        Returns:
            int: Element version
        """
        raise NotImplementedError
