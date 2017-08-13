# -*- coding: utf-8 -*-
from edxml.EDXMLEvent import EDXMLEvent
import edxml.transcode


class JsonTranscoder(edxml.transcode.Transcoder):

  ATTRIBUTE_MAP = {}
  """
  The ATTRIBUTE_MAP attribute is a dictionary mapping JSON attributes to EDXML
  event properties. The map is used to automatically populate the properties of
  the EDXMLEvent instances produced by the Generate method of the JsonTranscoder
  class. The keys may contain dots, indicating a subfield or positions within
  an array, like so::

      {'fieldname.0.subfieldname': 'property-name'}

  Note that the event structure will not be validated until the event is yielded by
  the Generate() method. This creates the possibility to add nonexistent properties
  to the attribute map and remove them in the Generate method, which may be convenient
  for composing properties from multiple JSON values, or for splitting the auto-generated
  event into multiple output events.
  """

  def Generate(self, Json, RecordTypeName, **kwargs):
    """

    Generates one or more EDXML events from the
    given JSON record, populating it with properties
    using the ATTRIBUTE_MAP class property.

    The JSON record can be passed either as a dictionary,
    an object, a dictionary containing objects or an object
    containing dictionaries. Dictionaries are allowed to contain
    lists or other dictionaries. For objects, the ATTRIBUTE_MAP
    will be used to access its attributes. These attributes
    may in turn be dictionaries, lists or other objects. Using
    dotted notation in ATTRIBUTE_MAP, you can extract pretty much
    everything from anything.

    This method can be overridden to create a generic
    event generator, populating the output events with
    generic properties that may or may not be useful to
    the record specific transcoders. The record specific
    transcoders can refine the events that are generated
    upstream by adding, changing or removing properties,
    editing the event content, and so on.

    Args:
      Json (dict, object): Decoded JSON data
      RecordTypeName (str): The JSON record type
      **kwargs: Arbitrary keyword arguments

    Yields:
      EDXMLEvent:
    """

    Properties = {}

    EventTypeName = self.TYPE_MAP.get(RecordTypeName, None)

    for JsonField, PropertyName in self.ATTRIBUTE_MAP.items():
      # Below, we parse dotted notation to find sub-fields
      # in the Json data.

      FieldPath = JsonField.split('.')
      if len(FieldPath) > 0:
        try:
          if type(Json) == dict:
            Value = Json.get(FieldPath[0])
          else:
            Value = getattr(Json, FieldPath[0])
        except AttributeError:
          try:
            Value = Json[int(FieldPath[0])]
          except (ValueError, IndexError):
            # Field not found in JSON, try next.
            continue
        for Field in FieldPath[1:]:
          try:
            if type(Value) == dict:
              Value = Value.get(Field)
            else:
              Value = getattr(Value, Field)
          except AttributeError:
            try:
              Value = Value[int(Field)]
            except (ValueError, IndexError):
              # Field not found in JSON.
              Value = None
              break

        if Value is not None:
          if type(Value) == list:
            Properties[PropertyName] = Value
          elif type(Value) == bool:
            Properties[PropertyName] = ['true' if Value else 'false']
          else:
            Properties[PropertyName] = [Value]

    yield EDXMLEvent(Properties, EventTypeName)
