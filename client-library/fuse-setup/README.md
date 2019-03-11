# Fuse-Helloworld
https://github.com/libfuse/libfuse/blob/579c3b03f57856e369fd6db2226b77aba63b59ff/include/fuse.h#L102-L577

https://engineering.facile.it/blog/eng/write-filesystem-fuse/

raw-commands history:  
    8  apt-get update
    9  apt-get install gcc fuse libfuse-dev make cmake
   10  echo $?
   11  apt-get install git
   12  git clone https://github.com/fntlnz/fuse-example.git
   13  ls
   14  vi fuse-example/fuse-example.c
   15  cd fuse-example/
   16  ls
   17  cmake -DCMAKE_BUILD_TYPE=Debug .
   18  make
   19  echo $?
   20  mkdir /tmp/example
   21  ./bin/fuse-example -d -s -f /tmp/example
   22  cd ..
   23  ls
   24  pwd
   25  git clone https://github.com/fusepy/fusepy.git
   26  apt-get install python
   27  ls
   28  cd fusepy/
   29  ls
   30  python setup.py install
   31  apt-get install pip
   32  apt-get install python-pip
   33  pip install setuptools
   34  ls
   35  python setup.py install
   36  echo $?
   37  ls
   38  cd examples/
   39  ls
   45  ls /tmp/
   46  mkdir /tmp/pyexample
   48  python memory.py /tmp/pyexample

raw-commands test history:

    7  ls -la /tmp/example/
    8  cat /tmp/example/file
    9  ls /tmp/pyexample/
   10  echo "adsflasjflads" /tmp/pyexample/
   11  echo "adsflasjflads" > /tmp/pyexample/file1
   12  cat /tmp/pyexample/file1