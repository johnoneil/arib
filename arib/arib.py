#!/usr/bin/env python 
# vim: set ts=2 expandtab:
'''
Module:arib.py
Desc: parsing Closed Captions from Japanese transport/elementary streams
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

  
''' 

import os
import os.path
from os.path import expanduser
import re
import uuid
import sys
import time
import argparse
import string
import struct

def get_byte(filepath):
  '''
  Read series of bytes from a file
  '''
  f = open(filepath, "rb")
  try:
    byte = f.read(1)
    while byte:
      yield byte
      byte = f.read(1)
  finally:
    f.close()

class GroupData:
  def __init__(self, f):
    self._stuffing_byte = struct.unpack('B', f.read(1))[0]
    print str(self._stuffing_byte)
    if(self._stuffing_byte is not 0x80):
      raise ValueError
    self._data_identifier = struct.unpack('B', f.read(1))[0]
    print str(self._data_identifier)
    if self._data_identifier is not 0xff:
      raise ValueError
    self._private_stream_id = struct.unpack('B', f.read(1))[0]
    print str(self._private_stream_id)
    if self._private_stream_id is not 0xf0:
      raise ValueError
    self._group_id = struct.unpack('B', f.read(1))[0]
    print str(self._group_id)
    self._group_link_number = struct.unpack('B', f.read(1))[0]
    print str(self._group_link_number)
    self._last_group_link_number = struct.unpack('B', f.read(1))[0]
    print str(self._last_group_link_number)
    self._data_group_size = struct.unpack('>H', f.read(2))[0]
    print 'data group size found is ' + str(self._data_group_size)
    self._payload = f.read(self._data_group_size)
    self._crc = struct.unpack('>H', f.read(2))[0]
    print 'crc value is ' + str(self._crc)

def next_group_data(filepath):
  f = open(filepath, "rb")
  try:
    group_data = GroupData(f)
    while group_data:
      yield group_data
      group_data = GroupData(f)
  finally:
    f.close()  
    
    


def main():
  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Elementary Stream.')
  parser.add_argument('infile', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  #parser.add_argument('-p', '--pid', help='Pid of stream .', type=str, default='')
  args = parser.parse_args()

  infilename = args.infile
  if not os.path.exists(infilename):
    print 'Please provide input Elemenatry Stream file.'
    os.exit(-1)
    
  #open our file and process each packet.
  #for byte in get_byte(infilename):
  #  #print str(byte)
  #  print '{0:x}'.format(ord(byte))

  for data_group in next_group_data(infilename):
    pass

if __name__ == "__main__":
  main()
