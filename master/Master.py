import ChuckServer.py
import sqlite.py
import getFileContent.py
import socket
import sys

# define the IP and address to blind, here we use the local address
master_address = ('localhost', 8080)

class Master:
    def _init_(self):
        self.chunkservers_number = 10
        self.chunksize = 10
    #    self.chunkrobin = 0
        self.serverrobin = 0
    #    self.filetable1 = {}  # file to chunk mapping
        self.filetable = {}  # file to chunk server mapping
        self.chunktable = {}  # chunkuuid to chunkserver mapping
        self.chunkservers = {}  # loc id to chunkserver mapping
        self.init_chunkservers()
        self.run()

    def init_chunkservers(self):
        for i in range(0, self.chunkservers_number):
            chunkserver = Chunkserver(i)
            self.chunkservers[i] = chunkserver

    def alloc(self, filename, num_chucks):  #alloc file to chunkservers
        serveruuids = []
        for i in range(0, 3):
            serverloc = self.serverrobin
            self.alloc_chunks(num_chucks, serverloc)
            serveruuids.append(serverloc)
            self.serverrobin = (self.serverrobin + 1) % self.chunkservers_number
        self.filetable[filename] = serveruuids
        # write into database
        sqlite.insert_file(filename, serveruuids)
        return serveruuids
    '''
    def alloc(self, filename, num_chunks):  # return ordered chunkuuid list
        chunkuuids = self.alloc_chunks(num_chunks)
        self.filetable[filename] = chunkuuids
        return chunkuuids
    '''
    def alloc_chunks(self, num_chunks, serverloc):
        # chunkuuids = []
        for i in range(0, num_chunks):
            chunkuuid = uuid.uuid1()
        #    chunkloc = self.chunkrobin
            self.chunktable[chunkuuid] = serverloc
        #    chunkuuids.append(chunkuuid)
        #    self.chunkrobin = (self.chunkrobin + 1) % self.chunkservers_number
        #return chunkuuids
    '''
    def alloc_append(self, filename, num_append_chunks):  # append chunks
        chunkuuids = self.filetable[filename]
        append_chunkuuids = self.alloc_chunks(num_append_chunks)
        chunkuuids.extend(append_chunkuuids)
        return append_chunkuuids
    '''
    def get_chunkservers(self):
        return self.chunkservers

    def get_chunkloc(self, chunkuuid):
        return self.chunktable[chunkuuid]

    def get_serveruuids(self, filename):
        return self.filetable[filename]

    def exists(self, filename):
        return True if filename in self.filetable else False

    def run(self):
        print >> sys.stderr, 'starting up on % s port %s' % master_address
        # instantiated a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # blind the socket to IP and port
        sock.bind(master_address)
        # set the socket to listen
        sock.listen(1)
        # here, it will be implemented to multi-thread later
        while True:
            # receive the request from client
            connection, client_address = sock.accept()
            print >> sys.stderr, 'waiting for a connection'
            try:
                # get the request data
                filename = connection.recv(1024)
                if filename:
                    # server reply to browser
                    connection.sendall(getFileContent.getHtmlFile(sqlite.get_chunkserver(filename)))
            finally:
                connection.close()


