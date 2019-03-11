import sqlite3

master_db = "master.db"

def create_table():
    with sqlite3.connect(master_db) as conn:
        print "Opened database successfully";
        c = conn.cursor()
        c.execute('''CREATE TABLE FilenameCsid(
                file_name CHAR(20) NOT NULL PRIMARY KEY,
           	    cs_id     INTEGER  NOT NULL,
           	    CHECK(cs_id > 0)
                );''')
        c.execute('''CREATE TABLE CsidIp(
        	    cs_id INTEGER NOT NULL PRIMARY KEY,
        	    ip    TEXT    NOT NULL,
        	    port  INTEGER NOT NULL,
        	    UNIQUE(ip, port),
        	    CHECK(LENGTH(ip) > 0),
        	    CHECK(cs_id > 0),
        	    CHECK(port > 0)
                );''')
        print "Table created successfully";
        return True

def get_chunkserver(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute('SELECT cs_id FROM FilenameCsid WHERE file_name=?',(filename,))
        for row in cursor:
            id = row[0]
        cursor = c.execute('SELECT ip, port FROM CsidIp WHERE cs_id=?',(id,))
        for row in cursor:
            ip = row[0]
            port = row[1]
        return (id, ip, port)


def exists(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute('SELECT file_name FROM FilenameCsid WHERE file_name=?',(filename,))
        if cursor.rowcount == 0:
            return True
        return False

def delete_file(filename):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute('SELECT cs_id FROM FilenameCsid WHERE file_name=?',(filename,))
        for row in cursor:
            id = row[0]
        cursor = c.execute('DELETE FROM FilenameCsid WHERE file_name=?',(filename,))
        cursor = c.execute('SELECT filename FROM FilenameCsid WHERE cs_id=?',(id,))
        if cursor.rowcount == 0:
            cur = c.execute('DELETE FROM CsidIp WHERE cs_id=?',(id,))
        # return True

def insert_file(filenamae, csid, ip, port):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute("INSERT INTO FilenameCsid (file_name, cs_id) VALUES (?,?)",(filenamae,csid))
        cursor = c.execute("INSERT INTO CsidIp (cs_id, ip, port) VALUES (?,?,?)",(csid,ip,port))
        # return True

def update_file_chunkserver(filenamae, csid):
    with sqlite3.connect(master_db) as conn:
        c = conn.cursor()
        cursor = c.execute("UPDATE FilenameCsid SET cs_id = ? WHERE file_name = ?",(filenamae,csid))
        # return True
