# NnGFS

To run chunkserver:
1. Create To Sync database  (In current directory of NGINX if running C server version)
   cat chunkserver/ToSyncMetadata.sql | sqlite3 sync.db
2. start replica script
   python replica.py
3. Start chunkserver: python2.7 -m chunkserver.cs
   or follow README in gfs-nginx to start C server.

upload a chunk
url -XPUT 'http://localhost:8080/?filename=filename2&chunk=2&backup=6,5' --data "adlsjfalsdfjals"

download a chunk

    curl -XGET 'http://localhost:8080/?filename=filename1&chunk=0'
