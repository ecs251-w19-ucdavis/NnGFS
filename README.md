# NnGFS
developer.md

To run chunkserver:
(First time) cat chunkserver/ToSyncMetadata.sql | sqlite3 sync.db
python2.7 -m chunkserver.cs

upload a chunk
url -XPUT 'http://localhost:8080/?filename=filename2&chunk=2&backup=6&backup=5' --data "adlsjfalsdfjals" --header 'content-length: 15'

download a chunk
curl -XGET 'http://localhost:8080/?filename=filename1&chunk=0'