#Annotations
Client: C   
Master Server: M  
Chunk Server: CS  
  
#Supported Operations
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

#Master Server Metadata stucture
```python
{file_name : [{i: {primary: [x, True], backup1: [y, False], backup2:[z, True]}}, {i+1: ...}, ...]}
```


# Pseudo-API 
TODO: finalize this
### C-M
#### create (file_name)
master chooses primary CS, backup1 CS, backup2 CS.
store {file_name, []} to MATADATA

 
