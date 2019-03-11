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


MASTER APIS:

# CREATE NEW FILE

 REQUEST  
```
curl -XPOST 'http://localhost:8080/?filename=myfile1'  
```
 RESPONSE  
```
cs_id, ip, port 
[
   [1, "127.0.0.1", 8888],
   [2, "127.0.0.1", 8889],
   [3, "127.0.0.1", 8890]
]
```
# Write a chunk

REQUEST
```
curl -XGET 'http://localhost:8080/?filename=myfile1&operation=write&end=81960'
```
RESPONSE
```
{
  "chunks":
          [
           [1, "127.0.0.1", 8888],
           [2, "127.0.0.1", 8889],
           [3, "127.0.0.1", 8890]
          ],
  "size": [81960]
}
```
# Read a chunk

REQUEST
```
curl -XGET 'http://localhost:8080/?filename=myfile1&operation=read'
```
RESPONSE
```
{
  "chunks":
          [
           [1, "127.0.0.1", 8888],
           [2, "127.0.0.1", 8889],
           [3, "127.0.0.1", 8890]
          ],
   "size": [81960]
}
```