import requests
import json
import random
import traceback

CS = 1024 * 1024
masterIp = 'http://localhost:'
masterPort = '8000'
masterUrl = masterIp + masterPort

import logging
logging.basicConfig(filename='example.log',level=logging.DEBUG)


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
    file_buffer = get_file_with_chunkserver(filename, addresses[0], chunk_id)
    return file_buffer

def put_file(filename, chunk_id, data):
    addresses = get_chunkserver_with_filename(filename)['chunks']
    backup_str = ','.join(['%d' % x[0] for x in addresses[1:]])
    put_file_with_chunkserver(filename, addresses[0], chunk_id, data, backup_str)
    return len(data)

def write(path, data, offset, fh):
    try:
        if (offset % CS == 0 and len(data) == CS):
            return put_file(path, offset/CS, data)
        # find the chunkserver to be updated
        end = offset % CS + len(data)
        file_buffer = get_file(path, offset/CS)
        print(len(file_buffer), end, offset % CS, len(data))
        if len(file_buffer) < end:
            return put_file(path, offset/CS, file_buffer[:offset % CS] + data)
        else:
            return put_file(path, offset/CS, file_buffer[:offset % CS] + data + file_buffer[(offset%CS) + len(data):])
    except:
        traceback.print_exc()
        return 0

def read(path, size, offset, fh):
    file_buffer = get_file(path, offset/CS)
    end = (offset+size) % CS
    if end == 0:
        end = -1
    return file_buffer[offset % CS: end]

#print(create_file('dtxt'))
#print(write('dtxt', 'a'*(CS/2), CS*3, 0))

print(write('dtxt', 'z'*4, CS*3 + CS/2 - 2, 0))
#print(read('dtxt', CS, 0, 0))


