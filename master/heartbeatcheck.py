import sqlite3
import requests
import traceback

import sys
import os
import time

def get_chunkservers():
    """
    return (tosync_id, path, ip, port) lists
    """
    with sqlite3.connect(cs_db) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT cs_id, ip, port
            FROM CsidIp
            """)
        return cur.fetchall()

def set_alive(live_csids):
    with sqlite3.connect(cs_db) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE CsidIp
            SET alive = 1
            WHERE cs_id in (%s)
            """ % ','.join(["?" for x in live_csids]),
            tuple(live_csids))

def set_dead(dead_csids):
    with sqlite3.connect(cs_db) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE CsidIp
            SET alive = 0
            WHERE cs_id in (%s)
            """ % ','.join(["?" for x in dead_csids]),
            tuple(dead_csids))

def check_alive(ip, port):
    url = "http://%s:%s/chunkserver/status" % (ip, str(port))
    try:
        r = requests.get(url)
        return True
    except:
        traceback.print_exc()
        return False

while True:
    global cs_db
    cs_db = sys.argv[1]
    live_csids = []
    dead_csids = []
    time.sleep(5)
    for (cs_id, ip, port) in get_chunkservers():
        if check_alive(ip, port):
            live_csids.append(cs_id)
        else:
            dead_csids.append(cs_id)
    set_alive(live_csids)
    set_dead(dead_csids)
