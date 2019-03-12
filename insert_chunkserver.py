import sqlite3
import traceback

DB_PATH = "/Users/bojun/Desktop/ECS251/project/master/master.db"

DB_TABLENAME = "CsidIp"

#CSs = [[1, "127.0.0.1", 8000]]
CSs = [[1, "127.0.0.1", 8002], [2, "127.0.0.1", 8003], [3, "127.0.0.1", 8004]]



with sqlite3.connect(DB_PATH) as conn:
    for (csid, ip, port) in CSs:
        try:
            conn.cursor().execute("""
                INSERT INTO %s (cs_id, ip, port)
                VALUES (?, ?, ?)
                """ % DB_TABLENAME,
                (csid, ip, port))
        except:
            traceback.print_exc()
            continue
