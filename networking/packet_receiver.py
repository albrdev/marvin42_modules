"""
@author: albrdev
@email: albrdev@gmail.com
@date: 2019-05-14
"""

import socket, select, array, struct, queue, fcntl, termios
from .packets import PacketHeader, PacketID

class PacketReceiver(object):
    """
    Base class for packet/data handling
    Derive from this class to make custom packet handling easier
    """
    __slots__ = ['__socket', '__sockets_read', '__sockets_write', '__response_queues', '__header_buffer']

    def __init__(self, host: tuple, max_connections: int = 10):
        self.__socket = socket.socket()
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Set socket option for reusing address to true (this prevents the "socket already in use" error when stopping and restarting daemon in a too fast order)

        self.__sockets_read = [ self.__socket ] # Server should read form itself to detect new, incomming connections
        self.__sockets_write = [ ]

        self.__response_queues = { }
        self.__header_buffer = { }

        self.__socket.bind(host) # Bind to a specific address
        self.__socket.listen(max_connections)

    def __del__(self):
        self.on_server_disconnect()

        for s in reversed(self.__sockets_read): # Close all sockets (including server itself)
            self.__close_socket(s)

        #self.__socket.close() # Is already closed indirectly by self.__close_socket

    def _available_bytes(self, fd) -> int:
        """
        Return available bytes that we can read on a socket
        """
        buffer = array.array('i', [0])
        fcntl.ioctl(fd, termios.FIONREAD, buffer)
        return buffer[0]

    def on_client_connected(self, host: tuple):
        """
        Called when a client connects
        Override this in subclass
        """
        pass

    def on_client_disconnected(self, host: tuple):
        """
        Called when a client disconnects
        Override this in subclass
        """
        pass

    def on_server_disconnect(self):
        """
        Called when this class is destroyed
        Override this in subclass
        """
        pass

    def __close_socket(self, s: socket.socket):
        """
        Closes a socket and cleanup all objects related to it
        """
        if s in self.__sockets_write:
            self.__sockets_write.remove(s)

        if s in self.__response_queues:
            del self.__response_queues[s]

        self.__sockets_read.remove(s)
        s.close()

    def __read_socket(self, s: socket.socket):
        """
        Handles sockets that has data to be read/incomming connections
        """
        if s is self.__socket: # If socket is servers own socket, we have a new client connecting
            connection, addr = s.accept() # Accept client
            connection.setblocking(0) # Asynchronous input

            # Store info about client
            self.__sockets_read.append(connection)
            self.__response_queues[connection] = queue.Queue()
            self.on_client_connected(addr)

        else: # A clients socket has data to be read
            header = self.__header_buffer.get(s.getpeername(), None) # Has this client sent data before? Get the previous data (header) sent
            n = header.size if header is not None else PacketHeader.SIZE # Get the expected size to read (as stated in the header) or (if the header doesnt exist, which means this is the first data from that client to be received) set the size to header size

            avail = self._available_bytes(s.fileno()) # Get size of the data awaiting to be read
            if avail < n: # Available data size is not (yet) sufficient
                if avail <= 0: # If we have data request with no size, the client has disconnected
                    self.on_client_disconnected(s.getpeername())
                    self.__close_socket(s)

                return # If size of the data is less than expected, wait for more in the next call

            data = s.recv(n) if n > 0 else None # Receive the acctual data
            if header is None: # If we don't have previous data form this client
                if data is None: # This is not expected
                    return

                header = PacketHeader._make(struct.unpack(PacketHeader.FORMAT, data)) # Unpack header data
                self.__header_buffer[s.getpeername()] = header # Associente this header to client
                if header.size > 0: # If expecting more data receive it in the next call
                    return

            # Here we are guaranteed to have a header, but not necessarily any data after that (i.e: header != None and (data == None or data != None))
            if self.on_data_received(header, data): # Call callback
                response = struct.pack(PacketHeader.FORMAT, int(PacketID.TRUE), 0) # Success packet to be sent back
            else:
                response = struct.pack(PacketHeader.FORMAT, int(PacketID.FALSE), 0) # Fail packet to be sent back

            self.__response_queues[s].put(response) # Queue response packet
            if s not in self.__sockets_write:
                self.__sockets_write.append(s) # Append cliet socket to write queue

            del self.__header_buffer[s.getpeername()] # Remove associated header from client as it's already processed

    def __write_socket(self, s: socket.socket):
        """
        Handles outgoing data (response packets)
        """
        try:
            data = self.__response_queues[s].get_nowait()
        except queue.Empty:
            self.__sockets_write.remove(s)
        except KeyError:
            pass
        else:
            s.send(data)

    def __except_socket(self, s: socket.socket):
        """
        Handles socket faults
        """
        self.__sockets_read.remove(s)
        if s in outputs:
            self.__sockets_write.remove(s)

        del self.__response_queues[s]
        s.close()

    def poll(self):
        """
        Updating method that checks for read/write/error and connecting/disconnecting clients
        Should be run within close intervals
        """
        rlist, wlist, xlist = select.select(self.__sockets_read, self.__sockets_write, self.__sockets_read)

        for s in rlist:
            self.__read_socket(s)

        for s in wlist:
            self.__write_socket(s)

        for s in xlist:
            self.__except_socket(s)
