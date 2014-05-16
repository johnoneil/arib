# vim: set ts=2 expandtab:
'''
Module: read.py
Desc: unpack data from binary files
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 13th 2014

'''
import struct

def ucb(f):
  '''Read unsigned char byte from binary file
  '''
  return struct.unpack('B', f.read(1))[0]

def usb(f):
  '''Read unsigned short from binary file
  '''
  return struct.unpack('>H', f.read(2))[0]

def ui3b(f):
  '''Read 3 byte unsigned short from binary file
  '''
  return struct.unpack('>I', '\x00'+ (f.read(3)))[0]

def uib(f):
  '''
  '''
  return struct.unpack('>L', f.read(4))[0]


