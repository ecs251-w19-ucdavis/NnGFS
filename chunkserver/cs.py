#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from threading import Lock
from urlparse import urlparse, parse_qs
import os

from util.fs_lock import ReadWriteLock
from util.duplicate import add_to_sync

ROOT_DIR="/tmp/"

localpath_to_rwlock = {}
mutex = Lock()

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

def read_unlock(local_path):
    _get(local_path).release_read()

def write_lock(local_path):
    _get(local_path).acquire_write()

def write_unlock(local_path):
    _get(local_path).release_write()


def _get_backup_servers(querys):
    # TODO id or ip
    return querys['backup']

def to_local_path(filename, chunk):
    return "%s/%d" % (to_local_dir(filename), chunk)

def to_local_dir(filename):
    return "%s%s" % (ROOT_DIR, filename)


def to_local_path_http_path(path):
    return "%s%s" % (ROOT_DIR, path)

PORT_NUMBER = 8080

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
        self.send_header('Content-type','application/octet-stream')
        self.end_headers()
        data = None
        read_lock(local_path)
        try:
            with open(local_path, 'r') as f:
                data = f.read()
        finally:
            read_unlock(local_path)
        self.wfile.write(data)
        return

    def do_PUT(self):
        querys = parse_qs(urlparse(self.path).query)
        print(querys)
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
            with open(local_path, 'w') as f:
                f.write(content)
        finally:
            write_unlock(local_path)
        # TODO: add to to_sync_metadata
        add_to_sync(filename, chunk, _get_backup_servers(querys))
        self.send_response(200)
        return

if __name__ == '__main__':
    try:
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(('', PORT_NUMBER), myHandler)
        print('Started http chunk server on port %d' % PORT_NUMBER)
        
        #Wait forever for incoming htto requests
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        server.socket.close()