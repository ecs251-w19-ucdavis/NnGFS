# gfs-nginx
sudo vi /usr/local/nginx/conf/nginx.conf

        location /write/ {
            root   html;
            index  index.html index.htm;
            gfs;
            csid cksr1;
            chunksize 64k;
            #max_batch 5;
            root_dir /tmp/;
        }
# master ip port
        location /gfs_put/ {
            proxy_pass http://127.0.0.1:8888;
        }


https://github.com/bwang0202/nginx-cs

./configure --add-module=/home/bojun/nginx/gfs-nginx
make
sudo /usr/local/nginx/sbin/nginx -s stop
sudo make install
sudo /usr/local/nginx/sbin/nginx
tail -f /usr/local/nginx/logs/error.log

8192 bytes per write request, configurable by changing read_client_Request file threshhold.
