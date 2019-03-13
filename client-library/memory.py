#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import requests
import json
import random
import traceback

CS = 128 * 1024
masterIp = 'http://localhost:'
masterPort = '8000'
masterUrl = masterIp + masterPort


def create_file(filename):
    data = {'filename': filename}
    r = requests.post(masterUrl, params=data)
    return json.loads(r.text)


def get_chunkserver_with_filename(filename):
    send_data = {'filename': filename, 'operation': 'read'}
    r = requests.get(masterUrl, params=send_data)
    data = json.loads(r.text)
    # print(r.text)
    return data

def put_file_with_master(filename, end):
    send_data = {'filename': filename, 'operation': 'write', 'end': end}
    r = requests.get(masterUrl, params=send_data)
    return json.loads(r.text)


def get_file_with_chunkserver(filename, address, id):
    cs_ip = address[1]
    cs_port = address[2]
    cs_url = 'http://' + cs_ip + ':' + str(cs_port) + "/chunkserver/?filename=%s&chunk=%d" % (filename, id)
    r = requests.get(cs_url)
    return json.loads(r.text)['data']

def put_file_with_chunkserver(filename, address, id, data, backup_str):
    cs_ip = address[1]
    cs_port = address[2]
    cs_url = 'http://' + cs_ip + ':' + str(cs_port) + "/chunkserver/?filename=%s&chunk=%d&backupcsid=%s" % (filename, id, backup_str)
    print(cs_url)
    r = requests.put(cs_url, data=data)
    return r.text

def get_file(filename, chunk_id):
    addresses = get_chunkserver_with_filename(filename)['chunks']
    for i in range(len(addresses)):
        try:
            file_buffer = get_file_with_chunkserver(filename, addresses[i], chunk_id)
            return file_buffer
        except:
            traceback.print_exc()
            continue

def put_file(filename, chunk_id, data, end):
    addresses = get_chunkserver_with_filename(filename)['chunks']
    put_file_with_master(filename, end)
    backup_str = ','.join(['%d' % x[0] for x in addresses[1:]])
    put_file_with_chunkserver(filename, addresses[0], chunk_id, data, backup_str)
    return len(data)

def write(path, data, offset):
    try:
        write_end = offset + len(data)
        if (offset % CS == 0 and len(data) == CS):
            return put_file(path, offset/CS, data, write_end)
        # find the chunkserver to be updated
        end = offset % CS + len(data)
        file_buffer = get_file(path, offset/CS)
        print(len(file_buffer), end, offset % CS, len(data))
        if len(file_buffer) < end:
            return put_file(path, offset/CS, file_buffer[:offset % CS] + data, write_end)
        else:
            return put_file(path, offset/CS, file_buffer[:offset % CS] + data + file_buffer[(offset%CS) + len(data):], write_end)
    except:
        traceback.print_exc()
        return 0

def read(path, size, offset):
    file_buffer = get_file(path, offset/CS)
    return file_buffer[offset % CS: (offset % CS) + size]

#print(create_file('dtxt'))
#print(write('dtxt', 'a'*(CS/2), CS*3, 0))

#print(write('dtxt', 'z'*4, CS*3 + CS/2 - 2, 0))
#print(read('dtxt', CS, 0, 0))


def clean(path):
    return path.lstrip('/')

class Memory(LoggingMixIn, Operations):
    'Example memory filesystem. Supports only one level of files.'

    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(
            st_mode=(S_IFDIR | 0o755),
            st_ctime=now,
            st_mtime=now,
            st_atime=now,
            st_nlink=2)

    def chmod(self, path, mode):
        self.files[path]['st_mode'] &= 0o770000
        self.files[path]['st_mode'] |= mode
        return 0

    def chown(self, path, uid, gid):
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid

    def create(self, path, mode):

        if path != '/':
            path = clean(path)

        self.files[path] = dict(
            st_mode=(S_IFREG | mode),
            st_nlink=1,
            st_size=0,
            st_ctime=time(),
            st_mtime=time(),
            st_atime=time())

        if path != '/':
            create_file(path)

        self.fd += 1
        return self.fd

    def getattr(self, path, fh=None):
        if path == '/':
            return self.files[path]
        path = clean(path)
        attrs = get_chunkserver_with_filename(path)
        print(attrs)
        if not attrs['chunks']:
            if path not in self.files:
                raise FuseOSError(ENOENT)
        else:
            if path not in self.files:
                raise FuseOSError(ENOENT)
            print(self.files[path])
            self.files[path]['st_size'] = attrs['size'][0]
        return self.files[path]

    def getxattr(self, path, name, position=0):
        attrs = self.files[path].get('attrs', {})

        try:
            return attrs[name]
        except KeyError:
            return ''       # Should return ENOATTR

    def listxattr(self, path):
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()

    def mkdir(self, path, mode):
        self.files[path] = dict(
            st_mode=(S_IFDIR | mode),
            st_nlink=2,
            st_size=0,
            st_ctime=time(),
            st_mtime=time(),
            st_atime=time())

        self.files['/']['st_nlink'] += 1

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        path = clean(path)
        return read(path, size, offset)

    def readdir(self, path, fh):
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    def readlink(self, path):
        return self.data[path]

    def removexattr(self, path, name):
        attrs = self.files[path].get('attrs', {})

        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR

    def rename(self, old, new):
        self.data[new] = self.data.pop(old)
        self.files[new] = self.files.pop(old)

    def rmdir(self, path):
        # with multiple level support, need to raise ENOTEMPTY if contains any files
        self.files.pop(path)
        self.files['/']['st_nlink'] -= 1

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        self.files[target] = dict(
            st_mode=(S_IFLNK | 0o777),
            st_nlink=1,
            st_size=len(source))

        self.data[target] = source

    def truncate(self, path, length, fh=None):
        # make sure extending the file fills in zero bytes
        # self.data[path] = self.data[path][:length].ljust(
        #     length, '\x00'.encode('ascii'))
        # self.files[path]['st_size'] = length
        return

    def unlink(self, path):
        self.data.pop(path)
        self.files.pop(path)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        path = clean(path)
        return write(path, data, offset)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    fuse = FUSE(Memory(), args.mount, foreground=True, allow_other=True, iosize=128*1024, direct_io=True)
