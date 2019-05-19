import socket, select, array, struct, queue, fcntl, termios
from .packets import PacketHeader, PacketID

class PacketReceiver(object):
    __slots__ = ['__socket', '__sockets_read', '__sockets_write', '__response_queues', '__header_buffer']

    def __init__(self, host: tuple, max_connections: int = 10):
        self.__socket = socket.socket()
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.__sockets_read = [ self.__socket ]
        self.__sockets_write = [ ]
        self.__response_queues = { }

        self.__header_buffer = { }

        self.__socket.bind(host)
        self.__socket.listen(max_connections)

    def __del__(self):
        self.on_server_disconnect()

        for s in reversed(self.__sockets_read):
            self.__close_socket(s)

        #self.__socket.close()

    def _available_bytes(self, fd) -> int:###
        buffer = array.array('i', [0])
        fcntl.ioctl(fd, termios.FIONREAD, buffer)
        return buffer[0]

    def on_client_connected(self, host: tuple):
        pass

    def on_client_disconnected(self, host: tuple):
        pass

    def on_server_disconnect(self):
        pass

    def __close_socket(self, s: socket.socket):
        if s in self.__sockets_write:
            self.__sockets_write.remove(s)

        if s in self.__response_queues:
            del self.__response_queues[s]

        self.__sockets_read.remove(s)
        s.close()

    def __read_socket(self, s: socket.socket):  
        if s is self.__socket:
            connection, addr = s.accept()
            connection.setblocking(0)
            self.__sockets_read.append(connection)
            self.__response_queues[connection] = queue.Queue()
            self.on_client_connected(addr)

        else:
            header = self.__header_buffer.get(s.getpeername(), None)
            n = header.size if header is not None else PacketHeader.SIZE

            avail = self._available_bytes(s.fileno())
            if avail < n:
                if avail <= 0:
                    self.on_client_disconnected(s.getpeername())
                    self.__close_socket(s)

                return

            data = s.recv(n) if n > 0 else None
            if header is None and n > 0:
                if data is None:
                    return

                self.__header_buffer[s.getpeername()] = PacketHeader._make(struct.unpack(PacketHeader.FORMAT, data))
            else:
                if self.on_data_received(header, data):
                    response = struct.pack(PacketHeader.FORMAT, int(PacketID.TRUE), 0)
                else:
                    response = struct.pack(PacketHeader.FORMAT, int(PacketID.FALSE), 0)

                self.__response_queues[s].put(response)
                if s not in self.__sockets_write:
                    self.__sockets_write.append(s)

                del self.__header_buffer[s.getpeername()]

    def __write_socket(self, s: socket.socket):
        try:
            data = self.__response_queues[s].get_nowait()
        except queue.Empty:
            self.__sockets_write.remove(s)
        except KeyError:
            pass
        else:
            s.send(data)

    def __except_socket(self, s: socket.socket):
        self.__sockets_read.remove(s)
        if s in outputs:
            self.__sockets_write.remove(s)

        del self.__response_queues[s]
        s.close()

    def poll(self):
        rlist, wlist, xlist = select.select(self.__sockets_read, self.__sockets_write, self.__sockets_read)

        for s in rlist:
            self.__read_socket(s)

        for s in wlist:
            self.__write_socket(s)

        for s in xlist:
            self.__except_socket(s)
