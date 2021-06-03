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

import edxml
from edxml.ontology.event_type_factory import EventTypeFactory


class RecordTranscoder(EventTypeFactory):
    """
    This is a base class that can be extended to implement record transcoders
    for the various input data record types that are processed by a
    particular TranscoderMediator implementation. The class extends the EventTypeFactory
    class, which is used to generate the event types for the events that will be
    produced by the record transcoder.
    """

    TYPE_MAP = {}
    """
    The TYPE_MAP attribute is a dictionary mapping input record type selectors
    to the corresponding EDXML event type names. This mapping is used
    by the transcoding mediator to find the correct record transcoder for
    each input data record.

    Note:
      When no EDXML event type name is specified for a particular input record
      type selector, it is up to the record transcoder to set the event type on
      the events that it generates.

    Note:
      The fallback record transcoder must set the None key to the name of the EDXML
      fallback event type.
    """

    PROPERTY_MAP = {}
    """
    The PROPERTY_MAP attribute is a dictionary mapping event type names to the property
    value selectors for finding property objects in input records. Each value in the
    dictionary is another dictionary that maps value selectors to property names. The
    exact nature of the value selectors differs between record transcoder implementations.
    """

    TYPE_PROPERTY_POST_PROCESSORS = {}
    """
    The TYPE_PROPERTY_POST_PROCESSORS attribute is a dictionary mapping EDXML event type names to property
    processors. The property processors are a dictionary mapping property names to processors. A processor
    is a function that accepts a value from the input field that corresponds with the property and returns
    an iterable yielding zero or more values which will be stored in the output event.
    The processors will be applied to input record values before using them to create output events.

    Example::

        {
          'event-type-name': {
            'property-a': lambda x: yield x.lower()
          }
        }

    """

    TYPE_AUTO_REPAIR_NORMALIZE = {}
    """
    The TYPE_AUTO_REPAIR_NORMALIZE attribute is a dictionary mapping EDXML event type names to properties
    which should be repaired automatically by normalizing their object values. This means that the transcoder
    is not required to store valid EDXML string representations in its output events. Rather, it may store any
    type of value which can be normalized into valid string representations automatically. Please refer to the
    :func:`~edxml.ontology.DataType.normalize_objects` method for a list of supported value types.
    The names of properties for which values may be normalized are specified as a list.
    Example::

      {'event-type-name': ['some-property']}
    """

    TYPE_AUTO_REPAIR_DROP = {}
    """
    The TYPE_AUTO_REPAIR_DROP attribute is a dictionary mapping EDXML event type names to properties
    which should be repaired automatically by dropping invalid object values. This means that the transcoder
    is permitted to store object values which cause the output event to be invalid. The EDXML writer will
    attempt to repair invalid output events. First, it will try to normalize object values when configured
    to do so. As a last resort, it can try to drop any offending object values.
    The names of properties for which values may be dropped are specified as a list.
    Example::

      {'event-type-name': ['some-property']}
    """

    def __init__(self):
        super().__init__()

        self._ontology = None  # type: edxml.ontology.Ontology

    def set_ontology(self, ontology):
        self._ontology = ontology
        return self

    def update_ontology(self, ontology, validate=True):
        self._ontology.update(ontology, validate)

    def generate(self, record, record_selector, **kwargs):
        """

        Generates one or more EDXML events from the
        given input record

        Args:
          record: Input data record
          record_selector (str): The selector matching the input record
          **kwargs: Arbitrary keyword arguments

        Yields:
          edxml.EDXMLEvent:
        """
        yield from ()

    def post_process(self, event, input_record):
        """

        Generates zero or more EDXML output events from the
        given EDXML input event. If this method is overridden by
        an extension of the RecordTranscoder class, all events generated
        by the generate() method are passed through this method for
        post processing. This allows the generated events to be
        modified or omitted. Or, multiple derivative events can be
        created from a single input event.

        The input record that was used to generate the input event
        is also passed as a parameter. Post processors can use this
        to extract additional information and add it to the input event.

        Args:
          event (edxml.EDXMLEvent): Input event
          input_record: Input record

        Yields:
          edxml.EDXMLEvent:
        """
        yield from ()

    def create_concepts(self):
        """
        This method may be used to generate generic EDXML
        concepts that are used by all record transcoders.
        """
        pass

    def create_object_types(self):
        """
        This method may be used to generate generic EDXML
        object types that are used by all record transcoders.
        """
        pass

    @classmethod
    def check_class_attributes(cls):

        super().check_class_attributes()

        existing_types = set(cls.TYPES)

        const_with_property_sub_keys = [
            'TYPE_PROPERTY_POST_PROCESSORS'
        ]

        const_with_property_lists = [
            'TYPE_AUTO_REPAIR_NORMALIZE', 'TYPE_AUTO_REPAIR_DROP'
        ]

        for event_type_name in existing_types:
            existing_properties = set(cls.TYPE_PROPERTIES.get(event_type_name, {}).keys())

            for constant_name in const_with_property_sub_keys:
                constant = getattr(cls, constant_name)
                if set(constant.get(event_type_name, {}).keys()).difference(existing_properties) != set():
                    raise ValueError(
                        f"{cls.__name__}.{constant_name} contains property names that are not in TYPE_PROPERTIES."
                    )

            for constant_name in const_with_property_lists:
                constant = getattr(cls, constant_name)
                if set(constant.get(event_type_name, [])).difference(existing_properties) != set():
                    raise ValueError(
                        f"{cls.__name__}.{constant_name} contains property names that are not in TYPE_PROPERTIES."
                    )

        const_with_event_type_keys = [
            'TYPE_PROPERTY_POST_PROCESSORS',
            'TYPE_AUTO_REPAIR_NORMALIZE', 'TYPE_AUTO_REPAIR_DROP',
        ]

        for constant_name in const_with_event_type_keys:
            constant = getattr(cls, constant_name)
            if isinstance(constant, dict) and set(constant.keys()).difference(existing_types) != set():
                raise ValueError(
                    f"{cls.__name__}.{constant_name} contains event type names that are not in the TYPES attribute."
                )

    def _post_process_properties(self, event_type_name, properties):
        for property_name in properties:
            if self.TYPE_PROPERTY_POST_PROCESSORS.get(event_type_name, {}).get(property_name):
                processed = []
                for value in properties[property_name]:
                    processed.extend(self.TYPE_PROPERTY_POST_PROCESSORS[event_type_name][property_name](value))
                properties[property_name] = processed
        return properties
