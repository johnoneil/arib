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
import sys
import read
from read import EOFError
import traceback

from closed_caption import CaptionStatementData
from closed_caption import CaptionManagementData
from struct import error as struct_error
from copy import copy

DEBUG = False


class DataGroupParseError(Exception):
  """ Custom Exception generated when parsing a DataGroup from a binary stream
  """
  pass

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
      print hex(self._stuffing_byte)
    if(self._stuffing_byte is not 0x80):
      raise DataGroupParseError("Initial stuffing byte not equal to 0x80: " + hex(self._stuffing_byte))

    self._data_identifier = read.ucb(f)
    if DEBUG:
      print hex(self._data_identifier)
    if self._data_identifier is not 0xff:
      raise DataGroupParseError("Initial data identifier is not equal to 0xff" + hex(self._data_identifier))

    self._private_stream_id = read.ucb(f)
    if DEBUG:
     print hex(self._private_stream_id)
    if self._private_stream_id is not 0xf0:
      raise DataGroupParseError("Private stream id not equal to 0xf0: " + hex(self._private_stream_id))

    self._group_id = read.ucb(f)
    if DEBUG:
        print 'group id ' + str((self._group_id >> 2)&(~0x20))
    self._group_link_number = read.ucb(f)
    if DEBUG:
        print str(self._group_link_number)
    self._last_group_link_number = read.ucb(f)
    if DEBUG:
      print str(self._last_group_link_number)
    if self._group_link_number != self._last_group_link_number:
      print("This is data group packet " + str(self._group_link_number) + " of " + str(self._last_group_link_number))
    self._data_group_size = read.usb(f)
    if DEBUG:
      print 'data group size found is ' + str(self._data_group_size)

    if not self.is_management_data():
      self._payload = CaptionStatementData(f)
    else:
      #self._payload = f.read(self._data_group_size)
      #self._payload = read.buffer(f, self._data_group_size)
      self._payload = CaptionManagementData(f)
    
    self._crc = read.usb(f)
    if DEBUG:
      print 'crc value is ' + str(self._crc)

    # TODO: check CRC value

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

def find_data_group_start(f):
  """
  Find the start of the next data group in a binary file
  :param f: file descriptor we're reading from typically opened 'rb'
  :return: Boolean describing whether we found a new start pattern or not
  """
  start_pattern = '\x80\xff\xf0'
  read_pattern = ''
  c = f.read(1)
  while c:
    filepos = f.tell()
    read_pattern += c
    if len(read_pattern) > 3:
      read_pattern = read_pattern[1:]
    if read_pattern == start_pattern:
      f.seek(filepos-3)
      return True
    c = f.read(1)
  return False

def next_data_group(filepath):
  f = open(filepath, "rb")
  try:
    data_group = DataGroup(f)
    while data_group:
      yield data_group
      try:
        data_group = DataGroup(f)
      except EOFError:
          break
      except Exception, err:
        print("Exception throw while parsing data group from .es")
        traceback.print_exc(file=sys.stdout)
        print("Looking for new data group in .es")
        found = find_data_group_start(f)
        if found:
          print("Data group found. Continuing.")
          continue
        print("Data group not found. Bailing.")
        break
  except EOFError:
    # we can quite rightly run into eof here. in that case just bail
    pass
  except Exception, err:
    print("Exception throw while parsing data group from .es")
    traceback.print_exc(file=sys.stdout)
  finally:
    f.close()

