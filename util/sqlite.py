# sqlite related utility functions
import sqlite3
import apsw

sync_db = 'sync.db'

def add_tosync(file, chunk_id, destination_ids):
    with apsw.Connection(sync_db, flags=apsw.SQLITE_OPEN_READWRITE) as conn:
        conn.setbusytimeout(5000)
        ls = [[file, chunk_id, x] for x in destination_ids]
        print(ls)
        conn.cursor().executemany("INSERT INTO ToSync (file_name, chunk_id, cs_id) VALUES (?, ?, ?);", ls)

def delete_file(filename):
    conn = sqlite3.connect('sync.db')
    c = conn.cursor()
    print ("Opened database successfully")

    query = "SELECT SEGMENT_ID from file WHERE FILE_NAME = " + filename
    fileCursor = c.execute(query)
    # delete from table segment
    for row in fileCursor:
        query = "DELETE from segment WHERE SEGMENT_ID = " + str(row[0])
        segCursor = c.execute(query)
    # delete from table file
    query = "DELETE from file WHERE FILE_NAME = " + filename
    fileCursor = c.execute(query)

    print ("Operation done successfully")
    conn.close()

def create_file(file_id, file_name, segment_id, primary_id, primary_status, primary_address, backup1_id, backup1_status, backup2_id, backup2_status):
    conn = sqlite3.connect('sync.db')
    c = conn.cursor()
    print ("Opened database successfully")

    query = "INSERT INTO file (FILE_ID, FILE_NAME, SEGMENT_ID) VALUES ("
    query = query + str(file_id) + file_name + str(segment_id) + ")"
    c.execute(query);

    query = "INSERT INTO segment (SEGMENT_ID, PRIMARY_ID, PRIMARY_STATUS, PRIMARY_ADDRESS, \
    BACKUP1_ID, BACKUP1_STATUS, BACKUP1_ADDRESS, BACKUP2_ID, BACKUP2_STATUS, BACKUP2_ADDRESS,) VALUES ("

    query = query + str(segment_id) + str(primary_id) + str(primary_status) + str(primary_address) + \
    str(backup1_id) + str(backup1_status) + str(backup1_address) + \
    str(backup2_id) + str(backup2_status) + str(backup2_address) + ")"

    c.execute(query);

    print ("Operation done successfully")
    conn.close()
