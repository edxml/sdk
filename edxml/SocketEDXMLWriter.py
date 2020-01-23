from edxml.SimpleEDXMLWriter import SimpleEDXMLWriter
import socket


class SocketEDXMLWriter(SimpleEDXMLWriter):
    """
    Socket EDXML stream writer

    Sets up a socket as a file and uses SimpleEDXMLWriter to write to it.
    """

    def __init__(self, address, validate=True):
        """
        Instantiate the socket writer by calling it with a host and port tuple.
        It creates a connection and writes to it.

        :param address: tuple of hostname or address and port of the target
        :param validate: Boolean, True by default
        """
        client_socket = socket.create_connection(address)
        # open a socket in write mode because EDXMLWriter requires this
        # set the buffer to 0 because however much lxml flushes, the data is not sent
        # also tried TCP_NODELAY to no effect
        socketfile = client_socket.makefile('wb', 0)
        super(self.__class__, self).__init__(socketfile, validate=validate)
