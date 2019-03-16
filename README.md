# NnGFS
Use python2.7.  
C version chunk server only tested on ubuntu 16.04  

To run chunkserver:  
1. Create 'ToSync' database  (In current directory of NGINX if running C server version)  ```
   cat chunkserver/ToSyncMetadata.sql | sqlite3 sync.db```
2. start replica script  
   ```python replica.py  ```  
3. Start Python chunkserver: ```python -m chunkserver.chunkserver /path/to/its/working/directory  ```
   Start C chunkserver:

    sudo vi /usr/local/nginx/conf/nginx.conf

            location /chunkserver/ {
                root   html;
                index  index.html index.htm;
                gfs;
                csid 1;
                chunksize 128k;
                root_dir /tmp/;
            }


Then in terminal, go to nginx directory

    ./configure --add-module=/home/bojun/nginx/gfs-nginx --with-ld-opt='-lsqlite3'
    make  
    sudo /usr/local/nginx/sbin/nginx -s stop  
    sudo make install  
    sudo /usr/local/nginx/sbin/nginx  


Orginal project https://github.com/bwang0202/gfs-nginx

To run master:
1. ```Python Master.py```  
2. Insert chunk server info into master database.  
3. start heartbeat check script. ```python heartbeachcheck.py /path/to/master.db```

To run client:
1. Create a directory  
2. Start FUSE virtual file system: ```python client.py /newly/created/directory```  
