import socket
import sys
import getFileContent

# define the IP and address to blind, here we use the local address
server_address = ('localhost', 8080)


class WebServer():
    def run(self):
        print >> sys.stderr, 'starting up on % s port %s' % server_address
        # instantiated a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # blind the socket to IP and port
        sock.bind(server_address)
        # set the socket to listen
        sock.listen(1)
        # here, it will be implemented to multi-thread later
        while True:
            # receive the request from client
            connection, client_address = sock.accept()
            print >> sys.stderr, 'waiting for a connection'
            try:
                # get the request data
                data = connection.recv(1024)
                if data:
                    # server reply to browser
                    connection.sendall(getFileContent.getHtmlFile(data))
            finally:
                connection.close()

if __name__ == '__main__':
    server = WebServer()
    server.run()
