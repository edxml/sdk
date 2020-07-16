# -*- coding: utf-8 -*-
import copy
import time

from edxml import EDXMLWriter
from edxml.error import EDXMLValidationError
# from edxml.ontology import *
from edxml.ontology import Ontology


class SimpleEDXMLWriter(object):
    """High level EDXML stream writer

    This class offers a simplified interface to
    the EDXMLWriter class. Apart from a simplified
    interface, it implements some additional features
    like buffering, post-processing, automatic merging
    of output events and latency control.

    The class is a Python context manager which will
    automatically flush the output buffer as soon as it
    goes out of scope.
    """

    def __init__(self, output=None, validate=True):
        """

        Create a new SimpleEDXMLWriter, generating an EDXML data stream.

        By default, the output will be fully validated. Optionally, validating the event
        objects can be disabled, or output validation can be completely disabled by setting
        Validate to True. This may be used to boost performance in case you know that
        the data will be validated at the receiving end, or in case you know that your
        generator is perfect. :)

        The Output parameter is a file-like object that will be used to send the XML data to.
        This file-like object can be pretty much anything, as long as it has a write() method
        and a mode containing 'a' (opened for appending). When the Output parameter is omitted,
        the generated XML data will be returned by the methods that generate output.

        Args:
         output (file, optional): a file-like object
         validate (bool`, optional): Validate the output (True) or not (False)

        Returns:
           SimpleEDXMLWriter:
        """

        self.__max_buf_size = 1024
        self.__curr_buffer_size = 0
        self.__output = output
        self.__validate = validate
        self.__max_latency = 0
        self.__last_write_time = time.time()
        self.__allow_repair_drop = {}
        self.__allow_repair_normalize = {}
        self.__ignore_invalid_events = False
        self.__log_invalid_events = False
        self.__log_repaired_events = False
        self.__event_buffers = {}
        self.__previous_event_buffers = {}
        self.__ontology = Ontology()
        self.__last_written_ontology_version = self.__ontology.get_version()
        self.__wrote_ontology_before = False
        self.__event_type_post_processors = {}
        self.__auto_merge = {}
        self.__writer = None
        self.__closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If writer exits due to an EDXML validation exception,
        # we will not flush the event output buffer. We do that to
        # prevent us from outputting invalid EDXML data. For other
        # kinds of exceptions, like KeyboardInterrupt, flushing the
        # output buffers is fine.
        self.close(flush=exc_type != EDXMLValidationError)

    def register_event_postprocessor(self, event_type_name, callback):
        """

        Register a post-processor for events of specified type. Whenever
        an event is submitted through the add_event() method, the supplied
        callback method will be invoked before the event is output. The
        callback must have the the same call signature as the add_event()
        method. The callback should not return anything.

        Apart from generating events, callbacks can also modify the event
        that is about to be outputted, by editing its call arguments.

        Args:
          event_type_name (str): Name of the event type
          callback (callable): The callback

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """

        if event_type_name not in self.__event_type_post_processors:
            self.__event_type_post_processors[event_type_name] = callback
        else:
            raise Exception(
                'Another post processor has already been registered for %s.' % event_type_name)

        return self

    def enable_auto_repair_drop(self, event_type_name, property_names):
        """

        Allows dropping invalid object values from the specified event
        properties while repairing invalid events. This will only be
        done as a last resort when normalizing object values failed or
        is disabled.

        Note:
          Dropping object values may still lead to invalid events.

        Note:
          This has no effect when object validation is disabled.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
           SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """
        self.__allow_repair_drop[event_type_name] = property_names

        return self

    def ignore_invalid_events(self, warn=False):
        """

        Instructs the EDXML writer to ignore invalid events.
        After calling this method, any event that fails to
        validate will be dropped. If Warn is set to True,
        a detailed warning will be printed, allowing the
        source and cause of the problem to be determined.

        Note:
          This has no effect when event validation is disabled.

        Args:
          warn (bool`, optional): Print warnings or not

        Returns:
           SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """
        self.__ignore_invalid_events = True
        self.__log_invalid_events = warn

        return self

    def enable_auto_repair_normalize(self, event_type_name, property_names):
        """

        Enables automatic repair of the property values of events of
        specified type. Whenever an invalid event is generated by the
        mediator it will try to repair the event by normalizing object
        values of specified properties.

        Args:
            event_type_name (str):
            property_names (List[str]):

        Returns:
            edxml.EDXMLWriter
        """
        if self.__writer:
            self.__writer.enable_auto_repair_normalize(event_type_name, property_names)
        else:
            self.__allow_repair_normalize[event_type_name] = property_names
        return self

    def log_repaired_events(self):
        """

        Enables logging of events that were invalid and needed
        to be repaired.

        Returns:
           SimpleEDXMLWriter: The SimpleEDXMLWriter instance

        """
        self.__log_repaired_events = True

        return self

    def auto_merge(self, event_type_name):
        """

        Enable auto-merging for events of specified event
        type. Auto-merging implies that colliding output events
        will be merged before outputting them. This may be useful
        to reduce the event output rate when generating large
        numbers of colliding events.

        Args:
          event_type_name (str): The name of the event type

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """
        self.__auto_merge[event_type_name] = True

        return self

    def add_ontology(self, ontology):
        """

        Add all definitions in specified ontology to the ontology that
        is written into the output EDXML stream.

        Args:
          ontology (edxml.ontology.Ontology): The EDXML ontology

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance

        """
        self.__ontology.update(ontology)
        return self

    def set_ontology(self, ontology):
        """

        Sets the output ontology to be used for producing the output
        stream. Changes to the specified ontology instance will be tracked,
        so it can be extended while writing events.

        Any previously added ontology information will be added to the
        specified Ontology instance, which may lead to validation errors.

        Args:
          ontology (edxml.ontology.Ontology): The EDXML ontology

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance

        """
        ontology.update(self.__ontology)
        self.__ontology = ontology
        self.__last_written_ontology_version = -1

        return self

    def reset_output(self, recover=False):
        """

        Starts writing a new EDXML data stream. The existing data stream
        is not closed before starting a new one. When the recover argument is
        set to True, the events that were last flushed to the output can be
        used to seed the new output buffer.

        This method can be used to recover when data gets lost while flushing
        the output.

        Args:
          recover (bool): Recover last flushed events

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance

        """

        output = b''

        self.__writer = EDXMLWriter(self.__output, self.__validate, self.__log_repaired_events)

        for event_type_name, property_names in self.__allow_repair_normalize.items():
            self.__writer.enable_auto_repair_normalize(event_type_name, property_names)

        for event_type_name, property_names in self.__allow_repair_drop.items():
            self.__writer.enable_auto_repair_drop(event_type_name, property_names)

        if self.__wrote_ontology_before:
            # We wrote an ontology before, let us write it again.
            output += self._write_ontology()

        if isinstance(self.__writer.get_output(), self.__writer.OutputBuffer):
            # The writer is writing into a memory buffer. Since this method is
            # typically used in error handling, and it is not very convenient
            # to have to process generated output in the error handler, we
            # will store the generated output in the output buffer. This way,
            # the data will be returned by the first regular data generation
            # method that gets called after us.
            self.__writer.get_output().write(output)

        # Reset state to reflect starting from scratch
        self.__last_written_ontology_version = self.__ontology.get_version()

        if self.__previous_event_buffers is None or recover is False:
            # Nothing to do
            return self

        # Seed the output buffer using the previously
        # flushed output buffer.
        for group_id in self.__previous_event_buffers:
            if group_id not in self.__event_buffers:
                self.__event_buffers[group_id] = {}
            for merge in self.__previous_event_buffers[group_id]:
                if merge:
                    if merge not in self.__event_buffers[group_id]:
                        self.__event_buffers[group_id][merge] = {}
                    for event_hash, events in self.__previous_event_buffers[group_id][merge].items():
                        self.__event_buffers[group_id][merge][event_hash] = events
                else:
                    if merge not in self.__event_buffers[group_id]:
                        self.__event_buffers[group_id][merge] = []
                    self.__event_buffers[group_id][merge].extend(
                        self.__previous_event_buffers[group_id][merge])

        self.__previous_event_buffers = None

        return self

    def add_event(self, event):
        """

        Add the specified event to the output stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as bytes.

        Args:
          event (edxml.EDXMLEvent): An EDXMLEvent instance

        Returns:
          bytes: Generated output XML data

        """
        event_type_name = event.get_type_name()

        if event_type_name in self.__event_type_post_processors:
            self.__event_type_post_processors[event_type_name](event)

        # TODO: We used to group events by type and source URI because the EDXML
        #       output format required it. This is no longer the case and the
        #       event group keys can be removed.
        event_group = 'group'
        if event_group not in self.__event_buffers:
            self.__event_buffers[event_group] = {True: {}, False: []}

        merge = event_type_name in self.__auto_merge
        if merge:
            # We need to compute the sticky hash, check
            # for collisions and merge if needed.
            event_hash = event.compute_sticky_hash(self.__ontology)

            if event_hash not in self.__event_buffers[event_group][merge]:
                self.__event_buffers[event_group][merge][event_hash] = [event]
            else:
                self.__event_buffers[event_group][merge][event_hash].append(event)
        else:
            self.__event_buffers[event_group][merge].append(event)

        self.__curr_buffer_size += 1

        return self.flush()

    def set_buffer_size(self, event_count):
        """

        Sets the buffer size for writing events to
        the output. The default buffer size is 1024
        events.

        Args:
         event_count (int): Maximum number of events

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """
        self.__max_buf_size = event_count
        return self

    def set_output_latency(self, latency):
        """

        Sets the output latency, in seconds. Setting this
        value to a positive value forces the writer to
        flush its buffers at least once every time the
        latency time expires. The default latency is zero,
        which means that output will be silent for as long
        as it takes to fill the input buffer.

        Args:
         latency (float): Maximum output latency (seconds)

        Returns:
          SimpleEDXMLWriter: The SimpleEDXMLWriter instance
        """
        self.__max_latency = latency
        return self

    def flush(self, force=False):
        """

        Request the writer to flush its output buffer. Unless the force
        argument is set to True, a buffer flush will only occur if needed.
        Flushing is needed when either the buffer is full or the configured
        output latency is exceeded.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as bytes.

        Args:
          force (bool): Force flushing or not

        Returns:
          bytes: Generated output XML data

        """

        output = b''

        if not self.__writer:
            # We did not create the EDXMLWriter yet.
            self.__writer = EDXMLWriter(self.__output, self.__validate, self.__log_repaired_events)

            for event_type_name, property_names in self.__allow_repair_normalize.items():
                self.__writer.enable_auto_repair_normalize(event_type_name, property_names)

            for event_type_name, property_names in self.__allow_repair_drop.items():
                self.__writer.enable_auto_repair_drop(event_type_name, property_names)

            # Instantiation of the writer produces output to initialize the stream,
            # so let us flush the writer to get it.
            output += self.__writer.flush()

        if self.__curr_buffer_size > self.__max_buf_size or \
           0 < self.__max_latency <= (time.time() - self.__last_write_time) or force:
            for group_id in self.__event_buffers:
                for merge in self.__event_buffers[group_id]:
                    output += self._flush_buffer(merge)

            self.__curr_buffer_size = 0
            self.__event_buffers = {}

            if self.__max_latency > 0:
                self.__last_write_time = time.time()

        return output

    def _write_ontology(self):
        output = b''
        output += self.__writer.add_ontology(self.__ontology)
        self.__last_written_ontology_version = self.__ontology.get_version()
        self.__wrote_ontology_before = True

        return output

    def _flush_buffer(self, merge):

        event_group_id = "group"

        if len(self.__event_buffers[event_group_id][merge]) == 0:
            return b''

        outputs = []

        if self.__ontology.is_modified_since(self.__last_written_ontology_version):
            # TODO: Rather than outputting a complete, new
            # ontology, we should only output the ontology
            # elements that are new or updated.
            outputs.append(self._write_ontology())

        if merge:
            for event_hash, events in self.__event_buffers[event_group_id][merge].items():
                if (len(events)) > 1:
                    first_event = self.__event_buffers[event_group_id][merge][event_hash].pop(
                    )
                    self.__event_buffers[event_group_id][merge][event_hash] = first_event.merge_with(
                        events, self.__ontology)
                else:
                    self.__event_buffers[event_group_id][merge][event_hash] = \
                        self.__event_buffers[event_group_id][merge][event_hash].pop(
                    )

        events = self.__event_buffers[event_group_id][merge].itervalues(
        ) if merge else self.__event_buffers[event_group_id][merge]

        for event in events:
            try:
                outputs.append(self.__writer.add_event(event))
            except EDXMLValidationError as Error:
                if self.__ignore_invalid_events:
                    if self.__log_invalid_events:
                        self.__writer.warning(
                            str(Error) + '\n\nContinuing anyways.\n')
                else:
                    raise

        # Below, we store a copy of the events we just serialized to EDXML and
        # clear the output buffer. We do that to allow implementing recovery.
        self.__previous_event_buffers = copy.deepcopy(self.__event_buffers)
        self.__event_buffers[event_group_id][merge] = {} if merge else []

        return b''.join(outputs)

    def close(self, flush=True):
        """

        Finalizes the output stream generation process. When this
        class is not used as a context manager, this method
        must be called to obtain a complete, valid output stream.

        By default, any remaining events in the output buffer will
        be written, unless flush is set to False.

        If no output was specified while instantiating this class,
        any generated XML data will be returned as bytes.

        Args:
          flush (bool): Flush output buffer

        Returns:
          bytes: Generated output XML data

        """

        if self.__closed:
            return b''

        outputs = []

        if not self.__writer:
            # We did not create the EDXMLWriter yet.
            self.__writer = EDXMLWriter(self.__output, self.__validate, self.__log_repaired_events)

            for event_type_name, property_names in self.__allow_repair_normalize.items():
                self.__writer.enable_auto_repair_normalize(event_type_name, property_names)

            for event_type_name, property_names in self.__allow_repair_drop.items():
                self.__writer.enable_auto_repair_drop(event_type_name, property_names)

            outputs.append(self._write_ontology())

        if flush and self.__ontology.is_modified_since(self.__last_written_ontology_version):
            outputs.append(self._write_ontology())

        if flush:
            outputs.append(self.flush(force=True))

        outputs.append(self.__writer.close())

        self.__writer = None
        self.__closed = True

        return b''.join(outputs)
