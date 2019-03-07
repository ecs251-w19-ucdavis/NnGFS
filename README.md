# NnGFS

NGINX ChunkServer has around 75% higher throughput then Python Chunkserver

To run python chunkserver:

    (First time) cat chunkserver/ToSyncMetadata.sql | sqlite3 sync.db
    python2.7 -m chunkserver.cs

To run C(NGINX) chunkserver:  
See README.md in gfs-nginx/

upload a chunk:

    curl -XPUT 'http://localhost:8080/?filename=filename2&chunk=2&backup=6&backup=5' \
    --data "adlsjfalsdfjals" --header 'content-length: 15'

download a chunk

    curl -XGET 'http://localhost:8080/?filename=filename1&chunk=0'
