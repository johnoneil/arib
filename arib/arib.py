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
from copy import copy
import read
import control_characters
import gl

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
  except struct.error:
    pass
  finally:
    f.close()

class DataGroup(object):
  '''Represents an arib Data Group packet structure as
  described in ARIB b-24 Table 9-1 on pg 172
  '''
  GroupA_Caption_Management = 0x0
  GroupB_Caption_Management = 0x20
  GroupA_Caption_Statement_lang1 = 0x1
  GroupA_Caption_Statement_lang2 = 0x2
  GroupA_Caption_Statement_lang3 = 0x3
  GroupA_Caption_Statement_lang4 = 0x4
  GroupA_Caption_Statement_lang5 = 0x5
  GroupA_Caption_Statement_lang6 = 0x6
  GroupA_Caption_Statement_lang7 = 0x7
  GroupA_Caption_Statement_lang8 = 0x8
  
  def __init__(self, f):
    self._stuffing_byte = read.ucb(f)
    print str(self._stuffing_byte)
    if(self._stuffing_byte is not 0x80):
      raise ValueError
    self._data_identifier = read.ucb(f)
    print str(self._data_identifier)
    if self._data_identifier is not 0xff:
      raise ValueError
    self._private_stream_id = read.ucb(f)
    print str(self._private_stream_id)
    if self._private_stream_id is not 0xf0:
      raise ValueError
    self._group_id = read.ucb(f)
    print 'group id ' + str((self._group_id >> 2)&(~0x20))
    self._group_link_number = read.ucb(f)
    print str(self._group_link_number)
    self._last_group_link_number = read.ucb(f)
    print str(self._last_group_link_number)
    self._data_group_size = read.usb(f)
    print 'data group size found is ' + str(self._data_group_size)
    if not self.is_management_data():
      self._payload = CaptionStatementData(f)
    else:
      self._payload = f.read(self._data_group_size)
    self._crc = read.usb(f)
    print 'crc value is ' + str(self._crc)

    #if this is caption data, analyze its structure
    if not self.is_management_data():
      payload = copy(self._payload)

  def is_management_data(self):
    '''Estimate whether the payload of this packet is 
    caption management data (as opposed to caption data itself.
    There appears to be some deviation from the standard, which
    states that the top 6 bits of _group_id should be zero or 0x20
    to qualify as managment data.
    '''
    return ((self._group_id >> 2)&(~0x20))==0

class CaptionStatementData(object):
  '''Represents a closed caption text wrapper
  Detailed in table 9-10 in ARIB STD b-24 PG 176
  '''
  def __init__(self, f):
    '''
    :param bytes: array of bytes payload
    '''
    self._TMD = read.ucb(f)>>6
    if self._TMD == 0x01 or self._TMD == 0X10:
      self.STM = 0#TODO: read four bytes
    else:
      self.STM = 0
    self._data_unit_loop_length = read.ui3b(f)
    print 'Caption statement: data unit loop length: ' + str(self._data_unit_loop_length)
    #self._payload = f.read(self._data_unit_loop_length)
    bytes_read = 0
    self._data_units = []
    while bytes_read < self._data_unit_loop_length:
      self._data_units.append(DataUnit(f))
      bytes_read += self._data_units[-1].size()

  def load_caption_statement_data(self, data):
    '''Load class contents from caption statement data payload
    '''
    pass

class StatementBody(object):
  '''Statement body (caption text) in Data Unit
  '''
  ID = 0x20
  def __init__(self, f, data_unit):
    self._unit_separator = data_unit._unit_separator
    self._data_unit_type = data_unit._data_unit_type
    if self._data_unit_type is not 0x20:
      print 'this is not caption data'
      raise ValueError
    self._data_unit_size = data_unit._data_unit_size
    #self._payload = f.read(self._data_unit_size)
    self._payload = StatementBody.parse_contents(f, self._data_unit_size)
    #print str(self._payload)

  @staticmethod
  def Type():
    return StatementBody.ID

  @staticmethod
  def parse_contents(f, bytes_to_read):
    '''
    Do complex reading of caption data from binary file.
    Return a list of statements and characters
    '''
    print 'going to read {bytes} bytes in binary file caption statement.'.format(bytes=bytes_to_read)
    statements = []
    bytes_read = 0
    while bytes_read<bytes_to_read:
      b = read.ucb(f)
      if b in control_characters.COMMAND_TABLE:
        statement = control_characters.COMMAND_TABLE[b](f)
        statements.append(statement)
        bytes_read += len(statement)
        print statement
      else:
        #statement = gl.TwoByteKanji(b, f)
        #statements.append(statement)
        #bytes_read += len(statement)
        #print statement
        bytes_read += 1
        print '--> {:#x}'.format(b)
    return bytes_read

class DataUnit(object):
  '''Data Unit structure as defined in ARIP B-24 Table 9-12 pg 157
  '''
  def __init__(self, f):
    self._unit_separator = read.ucb(f)
    if(self._unit_separator is not 0x1f):
      print 'Unit separator not found at start of data unit.'
      raise ValueError
    self._data_unit_type = read.ucb(f)
    print 'data unit type: ' + str(self._data_unit_type)
    self._data_unit_size = read.ui3b(f)
    print 'DataUnit size found to be: ' + str(self._data_unit_size)
    #self._payload = f.read(self._data_unit_size)
    self._payload = self.load_unit(f)
    
  def size(self):
    '''return size of inflated data unit in bytes
    '''
    return self._data_unit_size + 5

  def load_unit(self, f):
    if self._data_unit_type == StatementBody.ID:
      return StatementBody(f, self)
    else:
      return f.read(self._data_unit_size)

def next_data_group(filepath):
  f = open(filepath, "rb")
  try:
    data_group = DataGroup(f)
    while data_group:
      yield data_group
      data_group = DataGroup(f)
  except struct.error:
    pass
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
    
  for data_group in next_data_group(infilename):
    pass

if __name__ == "__main__":
  main()
