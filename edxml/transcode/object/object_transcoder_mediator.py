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

import edxml.transcode.mediator

from edxml.logger import log


class ObjectTranscoderMediator(edxml.transcode.mediator.TranscoderMediator):
    """
    This class is a mediator between a source of Python objects, also called
    input records, and a set of ObjectTranscoder implementations that can
    transcode the objects into EDXML events.

    Sources can instantiate the mediator and feed it records, while record
    transcoders can register themselves with the mediator in order to
    transcode the record types that they support. Note that we talk
    about "record types" rather than "object types" because mediators
    distinguish between types of input record by inspecting the attributes
    of the object rather than inspecting the Python object as obtained by
    calling type() on the object.
    """

    TYPE_FIELD = None
    """
    This constant must be set to the name of the item or attribute in the object
    that contains the input record type, allowing the TranscoderMediator to route
    objects to the correct record transcoder.

    If the constant is set to None, all objects will be routed to the fallback
    transcoder. If there is no fallback transcoder available, the record will not
    be processed.

    Note:
      The fallback transcoder is a record transcoder that registered itself
      using None as record type.
    """

    def register(self, record_type_identifier, transcoder):
        """

        Register a record transcoder for processing objects of specified
        record type. The same record transcoder can be registered for multiple
        record types.

        Note:
          Any record transcoder that registers itself using None
          as record_type_identifier is used as the fallback transcoder.
          The fallback transcoder is used to transcode any record for which
          no record transcoder has been registered.

        Args:
          record_type_identifier (Optional[str]): Name of the record type
          transcoder (ObjectTranscoder): ObjectTranscoder class
        """
        super().register(record_type_identifier, transcoder)

    def _get_transcoder(self, record_type_name=None):
        """

        Returns a ObjectTranscoder instance for transcoding
        records of specified type, or None if no record transcoder
        has been registered for the record type.

        Args:
          record_type_name (str): Name of the record type

        Returns:
          ObjectTranscoder:
        """
        return super()._get_transcoder(record_type_name)

    def process(self, input_record):
        """
        Processes a single input object, invoking the correct
        object transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        The object may optionally be a dictionary or act like one.
        Object transcoders can extract EDXML event object values from both
        dictionary items and object attributes as listed in the
        PROPERTY_MAP of the matching record transcoder. Using dotted notation
        the keys in PROPERTY_MAP can refer to dictionary items or
        object attributes that are themselves dictionaries of lists.

        Args:
          input_record (dict,object): Input object

        Returns:
          bytes: Generated output XML data

        """

        if self.TYPE_FIELD is None:
            # Type field is not set, which means we must use the
            # fallback transcoder.
            record_type = None
        else:
            try:
                record_type = input_record.get(self.TYPE_FIELD)
            except AttributeError:
                record_type = getattr(input_record, self.TYPE_FIELD)

        transcoder = self._get_transcoder(record_type)

        if not transcoder and record_type is not None:
            # No record transcoder available for record type,
            # use the fallback transcoder, if available.
            record_type = None
            transcoder = self._get_transcoder()

        if transcoder:
            if record_type is None and self.TYPE_FIELD and self._warn_fallback:
                log.warning(
                    'Input object has no "%s" field, passing to fallback transcoder. Record was: %s' %
                    (self.TYPE_FIELD, input_record)
                )

            self._transcode(input_record, record_type or '', record_type, transcoder)
        else:
            if self._warn_no_transcoder:
                if record_type is None and self.TYPE_FIELD:
                    log.warning(
                        'Input record has no "%s" field and no fallback transcoder available.' % self.TYPE_FIELD
                    )
                else:
                    log.warning(
                        'No record transcoder registered itself as fallback (record type None), '
                        'no %s event generated. Record was: %s' % (record_type, input_record)
                    )

        self._num_input_records_processed += 1

        return self._writer.flush()
