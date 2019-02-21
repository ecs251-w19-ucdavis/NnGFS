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

## C-M
#### read(file_name, i, pos, len)
```
if (file_name, i-th chunk) has a local file:
    read it*
    return data;
otherwise:
    return "NO DATA"
```

Note: * operations use local File System read/write lock. This ensures chunk reads/writes are atomic, but does not guarentee always reading from latest chunk data. (Client might read old data before a concurrent write has occured on that chunk server)  
But this design does ensure no interleaving of old/new data is ever possible within a chunk.