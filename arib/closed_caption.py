# vim: set ts=2 expandtab:
'''
Module: closed_caption.py
Desc: ARIB data group container
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

represents closed caption specific data within
an ARIB data group
  
'''

import read
from decoder import Decoder
import code_set
DEBUG = False

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
    if DEBUG:
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

def next_data_unit(caption_statement_data):
    current = 0
    while current < len(caption_statement_data._data_units):
        yield caption_statement_data._data_units[current]
        current += 1

class StatementBody(object):
  '''Statement body (caption text) in Data Unit
  '''
  ID = 0x20
  def __init__(self, f, data_unit):
    self._unit_separator = data_unit._unit_separator
    self._data_unit_type = data_unit._data_unit_type
    if self._data_unit_type is not 0x20:
      if DEBUG:
        print 'this is not caption data'
      raise ValueError
    self._data_unit_size = data_unit._data_unit_size
    #self._payload = f.read(self._data_unit_size)
    self._payload = StatementBody.parse_contents(f, self._data_unit_size)
    #print str(self._payload)

  def payload(self):
    return self._payload

  @staticmethod
  def Type():
    return StatementBody.ID

  @staticmethod
  def parse_contents(f, bytes_to_read):
    '''
    Do complex reading of caption data from binary file.
    Return a list of statements and characters
    '''
    if DEBUG:
      print 'going to read {bytes} bytes in binary file caption statement.'.format(bytes=bytes_to_read)
    statements = []
    bytes_read = 0
    #TODO: Check to see if decoder state is carred between packet processing
    #currently recreating the decoder (and therefore resetting its state)
    #on every packet paylod processing. This may be incorrect
    decoder = Decoder()
    line = ''
    while bytes_read<bytes_to_read:
      statement = decoder.decode(f)
      bytes_read += len(statement)
      statements.append(statement)
      #if isinstance(statement, code_set.Kanji) or isinstance(statement, code_set.Alphanumeric) \
      #  or isinstance(statement, code_set.Hiragana) or isinstance(statement, code_set.Katakana):
      #  if DEBUG:
      #    print statement #just dump to stdout for now
    #    line += str(statement)
    #if len(line)>0:
    #  print '{l}\n'.format(l=line)
    return statements


class DataUnit(object):
  '''Data Unit structure as defined in ARIP B-24 Table 9-12 pg 157
  '''
  def __init__(self, f):
    self._unit_separator = read.ucb(f)
    if(self._unit_separator is not 0x1f):
      if DEBUG:
        print 'Unit separator not found at start of data unit.'
      raise ValueError
    self._data_unit_type = read.ucb(f)
    if DEBUG:
      print 'data unit type: ' + str(self._data_unit_type)
    self._data_unit_size = read.ui3b(f)
    if DEBUG:
      print 'DataUnit size found to be: ' + str(self._data_unit_size)
    #self._payload = f.read(self._data_unit_size)
    self._payload = self.load_unit(f)

  def payload(self):
    return self._payload
    
  def size(self):
    '''return size of inflated data unit in bytes
    '''
    return self._data_unit_size + 5

  def load_unit(self, f):
    if self._data_unit_type == StatementBody.ID:
      return StatementBody(f, self)
    else:
      #return f.read(self._data_unit_size)
      read.buffer(f, self._data_unit_size)


