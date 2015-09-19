# vim: set ts=2 expandtab:
'''
Module: read.py
Desc: unpack data from binary files
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 13th 2014

'''
import struct

def split_buffer(length, buf):
  '''split provided array at index x
  '''
  #print "split-buffer******"
  a = []
  if len(buf)<length:
    return (a, buf)
  #print "length of buf is" + str(len(buf))
  for i in range(length):
    a.append(buf.pop(0))
  return (a,buf)

def dump_list(list):
  print(u' '.join(u'{:#x}'.format(x) for x in list))

def ucb(f):
  '''Read unsigned char byte from binary file
  '''
  if isinstance(f, list):
    n, f = split_buffer(1, f)
    return int(n[0])
  else:
    return struct.unpack('B', f.read(1))[0]

def usb(f):
  '''Read unsigned short from binary file
  '''
  if isinstance(f, list):
    n, f = split_buffer(2, f)
    return (n[0]<<8)|n[1]
  else:
    return struct.unpack('>H', f.read(2))[0]

def ui3b(f):
  '''Read 3 byte unsigned short from binary file
  '''
  if isinstance(f, list):
    n, f = split_buffer(3, f)
    return (n[0]<<16)|(n[1]<<8)|n[2]
  else:
    return struct.unpack('>I', '\x00'+ (f.read(3)))[0]

def uib(f):
  '''
  '''
  if isinstance(f, list):
    n, f = split_buffer(4, f)
    return (n[0]<<24)|(n[1]<<16)|(n[2]<<8)|n[0]
  else:
    return struct.unpack('>L', f.read(4))[0]

def buffer(f, size):
  '''Read N bytes from either a file or list
  '''
  if isinstance(f, list):
    n, f = split_buffer(size, f)
    return n
  else:
    return f.read(size)
