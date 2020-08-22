# -*- coding: utf-8 -*-

import edxml.transcode.mediator

from edxml.logger import log


class ObjectTranscoderMediator(edxml.transcode.mediator.TranscoderMediator):
    """
    This class is a mediator between a source of Python objects, also called
    input records, and a set of ObjectTranscoder implementations that can
    transcode the objects into EDXML events.

    Sources can instantiate the mediator and feed it records, while
    transcoders can register themselves with the mediator in order to
    transcode the record types that they support. Note that we talk
    about "record types" rather than "object types" because transcoders
    distinguish between types of input record by inspecting the attributes
    of the object rather than inspecting the Python object as obtained by
    calling type() on the object.
    """

    TYPE_FIELD = None
    """
    This constant must be set to the name of the item or attribute in the object
    that contains the input record type, allowing the TranscoderMediator to route
    objects to the correct transcoder.

    If the constant is set to None, all objects will be routed to the fallback
    transcoder. If there is no fallback transcoder available, the record will not
    be processed.

    Note:
      The fallback transcoder is a transcoder that registered itself as a transcoder
      using None as record type.
    """

    def register(self, record_type_identifier, transcoder):
        """

        Register a transcoder for processing objects of specified
        record type. The same transcoder can be registered for multiple
        record types. The Transcoder argument must be an ObjectTranscoder
        class or an extension of it. Do not pass in instantiated
        class, pass the class itself.

        Note:
          Any transcoder that registers itself as a transcoder using None
          as record_type_identifier is used as the fallback transcoder.
          The fallback transcoder is used to transcode any record for which
          no transcoder has been registered.

        Args:
          record_type_identifier (Optional[str]): Name of the record type
          transcoder (ObjectTranscoder): ObjectTranscoder class
        """
        super(ObjectTranscoderMediator, self).register(record_type_identifier, transcoder)

    def _get_transcoder(self, record_type_name=None):
        """

        Returns a ObjectTranscoder instance for transcoding
        records of specified type, or None if no transcoder
        has been registered for the record type.

        Args:
          record_type_name (str): Name of the record type

        Returns:
          ObjectTranscoder:
        """
        return super(ObjectTranscoderMediator, self)._get_transcoder(record_type_name)

    def process(self, input_record):
        """
        Processes a single input object, invoking the correct
        transcoder to generate an EDXML event and writing the
        event into the output.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        The object may optionally be a dictionary or act like one.
        Transcoders can extract EDXML event object values from both
        dictionary items and object attributes as listed in the
        PROPERTY_MAP of the matching transcoder. Using dotted notation
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
            # No transcoder available for record type,
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
                        'No transcoder registered itself as fallback (record type None), '
                        'no %s event generated. Record was: %s' % (record_type, input_record)
                    )

        self._num_input_records_processed += 1

        return self._writer.flush()
