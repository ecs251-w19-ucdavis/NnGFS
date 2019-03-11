import requests
import sqlite3
import traceback
import os

tosync_db_path = ""
batch = 10;

def _parse(path):
    file = os.path.basename(path)
    chunk = os.path.basename(os.path.dirname(path))
    return (file, chunk)

def copy_to_chunkserver(ip, port, path):
    file, chunk = _parse(path)
    with open(path, 'r') as f:
        r = requests.put("http://%s:%d/chunkserver/?filename=%s&chunk=%d" % (
            ip, port, file, chunk), data=f.read())
        print(r.text)
        return True

def get_next_batch():
    """
    return (tosync_id, path, ip, port) lists
    """
    with sqlite3.connect(tosync_db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT tosync_id, file_path ip, port
            FROM ToSync JOIN CsidIp USING using (cs_id)
            LIMIT 10;""")
        return cur.fetchall()


def remove_batch(tosync_ids):
    with sqlite3.connect(tosync_db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM ToSync
            WHERE tosync_id in (%s)""" % ",".join(["?" for x in tosync_ids]),
            tuple(tosync_ids))
        return


def main():
    while True:
        try:
            to_copy = get_next_batch()
            copied_tosync_ids = []
            for (tosync_id, path, ip, port) in get_next_batch():
                try:
                    if copy_to_chunkserver(ip, port, path):
                        copied_tosync_ids.add(tosync_id)
                except:
                    traceback.print_exc()
                    continue
            remove_batch(copied_tosync_ids)
        except:
            traceback.print_exc()
            continue