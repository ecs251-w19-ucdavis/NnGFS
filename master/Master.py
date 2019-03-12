import sqlite3

master_db = "master.db"

def create_table():
    with sqlite3.connect(master_db) as conn:
        print "Opened database successfully";
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS CsidIp(
                cs_id INTEGER NOT NULL PRIMARY KEY,
                ip    TEXT    NOT NULL,
                port  INTEGER NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(ip, port),
                CHECK(LENGTH(ip) > 0),
                CHECK(cs_id > 0),
                CHECK(port > 0),
                CHECK(count >= 0)
                );''')
        c.execute('''CREATE TABLE IF NOT EXISTS FilenameCsid(
                file_name CHAR(100) NOT NULL,
                cs_id     INTEGER  NOT NULL REFERENCES CsidIp(cs_id),
                file_size INTEGER NOT NULL DEFAULT 0,
                CHECK(cs_id > 0),
                CHECK(file_size >= 0)
                );''')
        print "Table created successfully";
        return True

def get_chunkserver(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT cs_id, ip, port
            FROM FilenameCsid
            JOIN CsidIp USING (cs_id)
            WHERE file_name=?""",(filename,))
        return c.fetchall()

def choose_chunkservers(num):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT cs_id, ip, port
            FROM CsidIp
            ORDER BY count DESC
            LIMIT ?
            """, (num, ))
        return c.fetchall()

def exists(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute('SELECT file_name FROM FilenameCsid WHERE file_name=?',(filename,))
        if cursor.rowcount == 0:
            return False
        return True

def delete_file(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute('DELETE FROM FilenameCsid WHERE file_name=?',(filename,))

def get_filesize(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT file_size FROM FilenameCsid
            WHERE file_name = ? LIMIT 1;
            """, (filename, ))
        size = c.fetchall()
        if not size:
            return 0
        else:
            return size[0]

def update_filesize(filename, size):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE FilenameCsid
            SET file_size = MAX(file_size, ?)
            WHERE file_name = ?;
            """, (size, filename))

def insert_file(filename, csids):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        t = []
        t2 = []
        for csid in csids:
            t.append(filename)
            t.append(csid[0])
            t2.append(csid[0])
        c.execute("""
            INSERT INTO FilenameCsid (file_name, cs_id)
            VALUES %s
            """ % (",".join(["(?,?)" for x in csids])),
            tuple(t))
        c.execute("""
            UPDATE CsidIp
            SET count = count + 1
            WHERE cs_id IN (%s)
            """ % ",".join(["?" for x in t2]),
            tuple(t2))


from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from threading import Lock
from urlparse import urlparse, parse_qs
import os
import requests
import json
import traceback

REPLICA_COUNT = 3
# define the IP and address to blind, here we use the local address
master_address = ('localhost', 8000)

class myHandler(BaseHTTPRequestHandler):
    
    #Handler for the GET requests
    def do_GET(self):
        """
        Read/Write file
        """
        querys = parse_qs(urlparse(self.path).query)
        filename = querys['filename'][0]
        operation = querys['operation'][0]
        size = 0
        if operation == "write":
            end = querys['end'][0]
            update_filesize(filename, end)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({'size': get_filesize(filename),
                'chunks': get_chunkserver(filename)}))

        return

    def do_POST(self):
        """
        Create new file
        """
        try:
            querys = parse_qs(urlparse(self.path).query)
            print(querys)
            filename = querys['filename'][0]
            csids = get_chunkserver(filename)
            if csids:
                if len(csids) != REPLICA_COUNT:
                    delete_file(filename)
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps(csids))
                    return
            csids = choose_chunkservers(REPLICA_COUNT)
            print(csids)
            insert_file(filename, csids)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(csids))
        except:
            traceback.print_exc()
        return


if __name__ == '__main__':
    try:
        create_table()
        #Create a web server and define the handler to manage the
        #incoming request
        server = HTTPServer(master_address, myHandler)
        print('Started http master server on port %d' % master_address[1])
        
        #Wait forever for incoming htto requests
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        server.socket.close()

