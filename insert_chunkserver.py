import sqlite3

DB_PATH = ""

DB_TABLENAME = "CsidIp"

#CSs = [[1, "127.0.0.1", 8000]]
CSs = [[]]





with sqlite3.connect(DB_PATH) as conn:
    for (csid, ip, port) in CSs:
        try:
            conn.cursor.execute("""
                INSERT INTO %s (cs_id, ip, port)
                VALUES (?, ?, ?)
                """ % DB_TABLENAME,
                (csid, ip, port))
        except:
            traceback.print_exc()
            continue
