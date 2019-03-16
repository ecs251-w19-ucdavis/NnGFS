import requests
import random
import string
import time

num_chunks = 1000
chunksize = 128 * 1024
data = ''.join([random.choice(string.ascii_letters 
            + string.digits) for n in range(chunksize)])

url = "http://localhost:80/chunkserver"

def read(filename):
	for chunk in range(num_chunks):
		r = requests.get("%s/?filename=%s&chunk=%d" % (url, filename, chunk % 2))

def write(filename):
	for chunk in range(num_chunks):
		r = requests.put("%s/?filename=%s&chunk=%d&backupcsid=%d,%d" % (url, filename, chunk % 2, 2, 3), data=data)

# DO IT
filename = ''.join([random.choice(string.ascii_letters 
            + string.digits) for n in range(5)])
# record write time
write_start = time.time()
for i in range(20):
	write(filename)
write_end = time.time()

print("%d chunks(%d bytes) written in %d seconds" % (num_chunks * 20, chunksize, write_end - write_start))
print("write throughput %d bytes per seconds" % (num_chunks * 20 * chunksize / (write_end - write_start)))
