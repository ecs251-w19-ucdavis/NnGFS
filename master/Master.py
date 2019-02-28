class Master:
    def _init_(self):
        self.chunkservers_number = 10
        self.chunksize = 10
        self.chunkrobin = 0
        self.filetable = {}  # file to chunk mapping
        self.chunktable = {}  # chunkuuid to chunkloc mapping
        self.chunkservers = {}  # loc id to chunkserver mapping
        self.init_chunkservers()

    def init_chunkservers(self):
        for i in range(0, self.chunkservers_number):
            chunkserver = Chunkserver(i)
            self.chunkservers[i] = chunkserver

    def alloc(self, filename, num_chunks):  # return ordered chunkuuid list
        chunkuuids = self.alloc_chunks(num_chunks)
        self.filetable[filename] = chunkuuids
        return chunkuuids

    def alloc_chunks(self, num_chunks):
        chunkuuids = []
        for i in range(0, num_chunks):
            chunkuuid = uuid.uuid1()
            chunkloc = self.chunkrobin
            self.chunktable[chunkuuid] = chunkloc
            chunkuuids.append(chunkuuid)
            self.chunkrobin = (self.chunkrobin + 1) % self.num_chunkservers
        return chunkuuids

    def alloc_append(self, filename, num_append_chunks):  # append chunks
        chunkuuids = self.filetable[filename]
        append_chunkuuids = self.alloc_chunks(num_append_chunks)
        chunkuuids.extend(append_chunkuuids)
        return append_chunkuuids

    def get_chunkservers(self):
        return self.chunkservers

    def get_chunkloc(self, chunkuuid):
        return self.chunktable[chunkuuid]

    def get_chunkuuids(self, filename):
        return self.filetable[filename]

    def exists(self, filename):
        return True if filename in self.filetable else False

    def delete(self, filename):  # rename for later garbage collection
        chunkuuids = self.filetable[filename]
        del self.filetable[filename]
        timestamp = repr(time.time())
        deleted_filename = "/hidden/deleted/" + timestamp + filename
        self.filetable[deleted_filename] = chunkuuids
        print "deleted file: " + filename + " renamed to " + \
              deleted_filename + " ready for gc"



