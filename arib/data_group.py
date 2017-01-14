# vim: set ts=2 expandtab:
'''
Module: data_group.py
Desc: ARIB data group container
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

Data group container is the primary container in an ARIB closed
caption and teletext elementary stream.
  
''' 

import read
from closed_caption import CaptionStatementData
from struct import error as struct_error
from copy import copy

DEBUG = False


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
    if DEBUG:
      print("__DATA_GROUP_START__")
    self._stuffing_byte = read.ucb(f)
    if DEBUG:
      print str(self._stuffing_byte)
    if(self._stuffing_byte is not 0x80):
      raise ValueError
    self._data_identifier = read.ucb(f)
    if DEBUG:
      print str(self._data_identifier)
    if self._data_identifier is not 0xff:
      raise ValueError
    self._private_stream_id = read.ucb(f)
    if DEBUG:
     print str(self._private_stream_id)
    if self._private_stream_id is not 0xf0:
      raise ValueError
    self._group_id = read.ucb(f)
    if DEBUG:
      print 'group id ' + str((self._group_id >> 2)&(~0x20))
    self._group_link_number = read.ucb(f)
    if DEBUG:
      print str(self._group_link_number)
    self._last_group_link_number = read.ucb(f)
    if DEBUG:
      print str(self._last_group_link_number)
    self._data_group_size = read.usb(f)
    if DEBUG:
      print 'data group size found is ' + str(self._data_group_size)

    if not self.is_management_data():
      self._payload = CaptionStatementData(f)
    else:
      #self._payload = f.read(self._data_group_size)
      self._payload = read.buffer(f, self._data_group_size)
    # we may be lacking a CRC?
    if len(f) >= 2:  # a short remains to be read
      self._crc = read.usb(f)
    else:
      self._crc = 0;
    if DEBUG:
      print 'crc value is ' + str(self._crc)

  def payload(self):
    return self._payload

  def is_management_data(self):
    '''Estimate whether the payload of this packet is 
    caption management data (as opposed to caption data itself.
    There appears to be some deviation from the standard, which
    states that the top 6 bits of _group_id should be zero or 0x20
    to qualify as management data.
    '''
    return ((self._group_id >> 2)&(~0x20))==0

def next_data_group(filepath):
  f = open(filepath, "rb")
  try:
    data_group = DataGroup(f)
    while data_group:
      yield data_group
      data_group = DataGroup(f)
  except struct_error:
    pass
  finally:
    f.close()

