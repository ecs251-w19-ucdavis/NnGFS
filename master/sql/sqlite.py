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
        return c.fetchall()[0]

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

