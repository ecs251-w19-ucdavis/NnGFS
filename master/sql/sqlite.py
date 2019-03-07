import sqlite3

def create_table():
    conn = sqlite3.connect('master.db')
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
    conn.commit()
    conn.close()
    return true

def get_chunkserver(filename):
    ids = []
    ips = []
    ports = []
    conn = sqlite3.connect('master.db')
    c = conn.cursor()
    cursor = c.execute('SELECT cs_id FROM FilenameCsid WHERE file_name=?',(filename,))
    for row in cursor:
        ids.append(row[0])
        cur = c.execute('SELECT ip, port FROM CsidIp WHERE cs_id=?',(row[0]),))
        for address in cur:
            ips.append(address[0])
            ports.append(address[1])
    return ids, ips, ports


def exists(filename):
    conn = sqlite3.connect('master.db')
    c = conn.cursor()
    cursor = c.execute('SELECT file_name FROM FilenameCsid WHERE file_name=?',(filename,))
    if cursor.rowcount == 0:
        conn.close()
        return True
    conn.close()
    return False

def delete_file(filename):
    conn = sqlite3.connect('master.db')
    c = conn.cursor()
    cursor = c.execute('SELECT cs_id FROM FilenameCsid WHERE file_name=?',(filename,))
    for row in cursor:
        id = row[0]
    cursor = c.execute('DELETE FROM FilenameCsid WHERE file_name=?',(filename,))
    cursor = c.execute('SELECT filename FROM FilenameCsid WHERE cs_id=?',(id,))
    if cursor.rowcount == 0:
        cur = c.execute('DELETE FROM CsidIp WHERE cs_id=?',(id,))
    conn.commit()
    conn.close()
    # return True

def insert_file(filenamae, csids):
    conn = sqlite3.connect('master.db')
    c = conn.cursor()
    cursor = c.execute("INSERT INTO FilenameCsid (file_name, cs_id) VALUES (?,?)",(filenamae,csids[0]))
    cursor = c.execute("INSERT INTO FilenameCsid (file_name, cs_id) VALUES (?,?)",(filenamae,csids[1]))
    cursor = c.execute("INSERT INTO FilenameCsid (file_name, cs_id) VALUES (?,?)",(filenamae,csids[2]))
    conn.commit()
    # cursor = c.execute("INSERT INTO CsidIp (cs_id, ip, port) VALUES (?,?,?)",(csid,ip,port))
    conn.close()
    # return True

def update_file_chunkserver(filenamae, csid):
    conn = sqlite3.connect('master.db')
    c = conn.cursor()
    cursor = c.execute("UPDATE FilenameCsid SET cs_id = ? WHERE file_name = ?",(filenamae,csid))
    conn.commit()
    conn.close()
    # return True
