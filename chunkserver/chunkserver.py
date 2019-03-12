#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from threading import Lock
from urlparse import urlparse, parse_qs
import os
import requests
import sys
import threading
import sqlite3
import traceback
import json

class ReadWriteLock:
    """ A lock object that allows many simultaneous "read locks", but
    only one "write lock." """

    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        """ Acquire a read lock. Blocks only if a thread has
        acquired the write lock. """
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()

    def release_read(self):
        """ Release a read lock. """
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notifyAll()
        finally:
            self._read_ready.release()

    def acquire_write(self):
        """ Acquire a write lock. Blocks until there are no
        acquired read or write locks. """
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """ Release a write lock. """
        self._read_ready.release()

localpath_to_rwlock = {}
mutex = Lock()

MASTER_URL = "http://localhost:8000"

# sqlite related utility functions
import apsw

sync_db = 'sync.db'

def add_tosync(file_path, destination_id1, destination_id2):
    with sqlite3.Connection("%s/%s" % (ROOT_DIR, sync_db)) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO ToSync (cs_id, file_path)
            VALUES (?, ?), (?, ?);
            """, (destination_id1, file_path, destination_id2, file_path))

def create_table():
    with sqlite3.connect("%s/%s" % (ROOT_DIR, sync_db)) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ToSync (
                        tosync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cs_id INTEGER NOT NULL,
                        file_path TEXT NOT NULL,
                        --
                        UNIQUE (cs_id, file_path),
                        CHECK(LENGTH(file_path) > 0),
                        CHECK(cs_id > 0)
                    );''')
        c.execute('''CREATE TABLE IF NOT EXISTS CsidIp (
                        cs_id INTEGER NOT NULL PRIMARY KEY,
                        ip TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        --
                        UNIQUE(ip, port),
                        CHECK(LENGTH(ip) > 0),
                        CHECK(cs_id > 0),
                        CHECK(port > 0)
                    );''')
        return True

def _get(local_path):
    mutex.acquire()
    try:
        if local_path not in localpath_to_rwlock:
            localpath_to_rwlock[local_path] = ReadWriteLock()
        return localpath_to_rwlock[local_path]
    finally:
        mutex.release()

def read_lock(local_path):
    _get(local_path).acquire_read()
    return

def read_unlock(local_path):
    _get(local_path).release_read()
    return

def write_lock(local_path):
    _get(local_path).acquire_write()
    return

def write_unlock(local_path):
    _get(local_path).release_write()
    return

def to_local_path(filename, chunk):
    return "%s/%d" % (to_local_dir(filename), chunk)

def to_local_dir(filename):
    return "%s/%s" % (ROOT_DIR, filename)


def to_local_path_http_path(path):
    return "%s%s" % (ROOT_DIR, path)

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):
    
    #Handler for the GET requests
    def do_GET(self):
        # Send the html message
        querys = parse_qs(urlparse(self.path).query)
        filename = querys['filename'][0]
        chunk = int(querys['chunk'][0]) ## TODO batch me
        local_path = to_local_path(filename, chunk)
        self.send_response(200)
        self.send_header('Content-Type','application/octet-stream')
        self.end_headers()

        data = ""
        read_lock(local_path)
        try:
            print(local_path)
            with open(local_path, 'r') as f:
                data = f.read()
        finally:
            read_unlock(local_path)
            self.wfile.write(json.dumps({"data":data}))
        return

    def do_PUT(self):
        querys = parse_qs(urlparse(self.path).query)
        filename = querys['filename'][0]
        chunk = int(querys['chunk'][0])
        local_path = to_local_path(filename, chunk)
        local_dir = to_local_dir(filename)
        length = int(self.headers['Content-Length'])
        content = self.rfile.read(length)
        write_lock(local_path)
        try:
            if not os.path.exists(local_dir):
                os.mkdir(local_dir)
            print(local_path)
            with open(local_path, 'w') as f:
                f.write(content)
        except:
            traceback.print_exc()
        finally:
            write_unlock(local_path)
        #tell_master(filename, chunk, "csidpython1")
        # TODO: add to to_sync_metadata
        splited = querys['backupcsid'][0].split(',')
        print(local_path, splited[0], splited[1])
        add_tosync(local_path, splited[0], splited[1])
        self.send_response(200)
        return

if __name__ == '__main__':
    try:
        #Create a web server and define the handler to manage the
        global ROOT_DIR, PORT_NUMBER
        ROOT_DIR=sys.argv[1]
        PORT_NUMBER=int(sys.argv[2])
        create_table()
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
        print('Started http chunk server on port %d' % PORT_NUMBER)
        
        #Wait forever for incoming htto requests
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        server.socket.close()