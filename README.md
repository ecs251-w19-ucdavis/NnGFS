# NnGFS
developer.md

To run chunkserver:
python2.7 -m chunkserver.cs

upload a chunk
curl -XPUT 'http://localhost:8080/?filename=filename2&chunk=2' --data "adlsjfalsdfjals" --header 'content-length: 15'

download a chunk
curl -XGET 'http://localhost:8080/?filename=filename1&chunk=0'