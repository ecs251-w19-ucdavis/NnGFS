# sqlite related utility functions
import apsw

sync_db = 'sync.db'

def add_tosync(file, chunk_id, destination_ids):
    with apsw.Connection(sync_db, flags=apsw.SQLITE_OPEN_READWRITE) as conn:
        conn.setbusytimeout(5000)
        ls = [[file, chunk_id, x] for x in destination_ids]
        print(ls)
        conn.cursor().executemany("INSERT INTO ToSync (file_name, chunk_id, cs_id) VALUES (?, ?, ?);", ls)