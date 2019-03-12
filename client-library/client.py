import requests
import json
import random

CS = 1024 * 1024
masterIp = 'http://localhost:'
masterPort = '8080'
masterUrl = masterIp + masterPort


def create_file(filename):
    data = {'filename': filename}
    r = requests.post(masterUrl, params=data)
    return json.load(r.text)


def get_chunkserver_with_filename(filename):
    send_data = {'filename': filename, 'operation': 'read'}
    r = requests.get(masterUrl, params=send_data)
    data = json.load(r.text)
    # print(r.text)
    return data[random.randint(0, 2)]


def get_file_with_chunkserver(filename, data, id):
    cs_ip = data[1]
    cs_port = data[2]
    cs_url = cs_ip + ':' + cs_port + "chunkserver/"
    send_data = {'filename': filename, 'chunk': id}
    r = requests.get(cs_url, params=send_data)
    return r.text

def put_file_with_chunkserver(filename, address, id, data, backup_str):
    cs_ip = data[1]
    cs_port = data[2]
    cs_url = cs_ip + ':' + cs_port + "/chunkserver/?filename=%s&chunk=%d&backupcsid=%s" % (filename, id, backup_str)
    r = requests.put(cs_url, data=data)
    return r.text

def get_file(filename, chunk_id):
    addresses = get_chunkserver_with_filename(filename)
    file_buffer = get_file_with_chunkserver(filename, addresses[0], chunk_id)
    return file_buffer

def put_file(filename, chunk_id, data):
    addresses = get_chunkserver_with_filename(filename)
    backup_str = ','.join([x[0] for x in addresses[1:]])
    put_file_with_chunkserver(filename, addresses[0], chunk_id, data, backup_str)
    return len(data)

# def update_file(filename):
# def delete_file(filename):


r = requests.get('https://api.github.com/events')
print r.text

# create_file('xxx.txt')
# get_chunkserver_with_filename('xxx.txt')


def write(self, path, data, offset, fh):
    try:
        # find the chunkserver to be updated
        end = (offset + len(data)) % CS
        file_buffer = get_file(path, offset/CS)
        if len(file_buffer) < end:
            new_buffer = "0" * end
            new_buffer[:len(file_buffer)] = file_buffer
            file_buffer = new_buffer
        file_buffer[offset % CS: (offset+len(data)) % CS] = data
        # write to chunkserver
        return put_file(path, offset/CS, file_buffer)
    except:
        return 0


def read(self, path, size, offset, fh):
    file_buffer = get_file(path, offset/CS)
    return file_buffer[offset % CS: (offset+size) % CS]
