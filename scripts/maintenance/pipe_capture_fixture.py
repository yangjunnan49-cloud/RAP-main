"""Fixed BPC0 child, binary pipes only, no files or descendant processes."""
import os
import sys
import time

mode=sys.argv[1]
if mode=='normal':
    os.write(1,b'hello-out\n');os.write(2,b'hello-err\n')
elif mode=='stdout_overflow':os.write(1,b'O'*4096)
elif mode=='stderr_overflow':os.write(2,b'E'*4096)
elif mode=='both_flood':
    for _ in range(128):
        os.write(1,b'O'*64);os.write(2,b'E'*64)
elif mode=='nonzero':
    os.write(2,b'planned exit7\n');sys.exit(7)
elif mode=='timeout':time.sleep(10)
elif mode=='empty':pass
elif mode=='binary':os.write(1,b'\xff\x00\xfe')
else:raise ValueError(mode)
