# Annotations
Client: C   
Master Server: M  
Chunk Server: CS  
Primary Chunk Server: CS\_P  
Backup Chunk Server 1: CS\_B1  
Backup Chunk Server 2: CS\_B2  
64MB is chunk size.  
  
# Supported Operations
#### create file, create(file_name)
Create an empty file with file_name.  
Note one cluster only has one namespace.  
Note no model of directories is supported.
#### read from file, read(file_name, pos, len)
Read len bytes starting at position pos from file_name.  
Similar to open() then lseek(pos)
#### write to file, write(file_name, pos, data)
Write data to file_name, starting from position pos.  
Similar to open() then lseek(pos)

# Master Server METADATA stucture
```
file_name:[  
   {  
      i:{  
         primary:[  
            x, True
         ],
         backup1:[  
            y, False
         ],
         backup2:[  
            z, True
         ]
      }
   },
   ...
]
```
This means for file file_name, primary copy of i-th chunk is at chunk server x and is already uploaded, first backup is at chunk server y and is not yet uploaded, second backup is at chunk server z and is already uploaded.

# Pseudo-APIs and effects
TODO: finalize/formalize this.
## C-M
#### create (file_name)
master chooses primary CS, backup1 CS, backup2 CS.  
store {file_name, []} to MATADATA  
return to client "OK".

#### write (file_name, pos, len)
```
start = pos/64MB, end = pos + len / 64MB
res = []
## Optimize by arranging chunks of same file to same chunk servers
## So that clients have a better chance to batch requests.
for i = start .. end // parallel
    acquire write lock (file_name, i)
    if METADATA has no file_name, i-th chunk:
        x, y, z = find 3 "not busy" chunk server
        set METADATA[file_name][i] = {
                primary: [x, False],
                backup1: [y, False],
                backup2: [z, False]};
    release write lock
    append METADATA[file_name][i]
return res to client
```

#### read (file_name, pos, len)
```
start = pos/64MB, end = pos + len / 64MB
res = []
for i = start .. end // parallel
    acquire read lock (file_name, i)
    if METADATA has no file_name, i-th chunk:
        res.append("invalid chunk i")
    else
        append(METADATA[file_name][i]);
    release read lock (file_name, i);
return res to client
```

## CS-M
#### heartbeat(self)
#### completed(file_name, i, self)
file_name's i-th chunk is completed on CS self.  
Master sets
```
METADATA[file_name][i][?:self] = True
```

## C-CS\_P, CS\_P-CS\_B1, CS\_P-CS\_B2
#### write(file_name, i, pos, data, {primary x, backup1 y, backup2 z})
```
# Clients should batch requests to reduce TCP handshake overhead
# or maintain some type of connection pool.
If (file_name, i-th chunk) has a local file:
    update it*
    return "OK" to client
Else
    create a local file and write to it*
    return "OK" to client
CS-M: completed(file_name, i, self)
if self is primary x:
    CS_P-CS_B1: write(file_name, i, pos, data, {...})
    CS_P-CS_B2: write(file_name, i, pos, data, {...})
```

## C-CS
#### read(file_name, i, pos, len)
```
# Clients should batch requests to reduce TCP handshake overhead
# or maintain some type of connection pool.
if (file_name, i-th chunk) has a local file:
    read it*
    return data;
otherwise:
    return "NO DATA"
```

Note: * operations use local File System read/write lock. This ensures chunk reads/writes are atomic, but does not guarentee always reading from latest chunk data. (Client might read old data before a concurrent write has occured on that chunk server)  
But this design does ensure no interleaving of old/new data is ever possible within a chunk.

# Optimization to do
1. Chunks of same file should be in same chunkserver set as much as possible.
2. Client batch read/write requests for consecutive chunks read/write.
3. Client keep TCP connection alive or maintain some type of connection pool to reduce TCP handshake overhead.
4. Performance: Python HTTP server + python thread sync read/write lock ---> NGINX + POSIX record process read/write locks (fcntl)




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