# vim: set ts=2 expandtab:
'''
Module: decoder.py
Desc: stateful arib teletext decoder
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Friday, March 15th 2014

'''

import read
from control_characters import is_control_character
from control_characters import handle_control_character
import code_set


def is_gl_character(char):
  '''Is the current character in the GL area
  ARIB STD-B24 figure 7-1
  '''
  ub = char >> 4
  #print 'is_gl_char char:{char} ub: {ub}'.format(char=char, ub=ub)
  return char != 0x20 and char != 0xa0 and ub > 0x01 and ub < 0x08

def is_gr_character(char):
  '''Is the current character in the GR area
  ARIB STD-B24 figure 7-1
  '''
  ub = char >> 4
  return ub >0x09

class Decoder(object):
  '''Decode a stream of bytes into an array
  of classes representing a decoded teletext packet payload
  '''
  def __init__(self):
    '''Init decoding of code table areas to defaults
    '''
    #default encoding 'designations'
    self._G0 = code_set.Kanji.decode
    #self._G1 = code_set.Alphanumeric()
    #self._G2 = code_set.Hiragana()
    #self._G3 = code_set.Macro()

    #default code table 'invocations'
    self._GL = self._G0
    #self._GR = self._G2

  def decode(self, f):
    '''Return an object representing the current character
    '''
    b = read.ucb(f)
    print '-->{:02x}'.format(b)
    #the interpretation and how many more bytes we have to read
    #depends upon:
    #1) What code table is this character in? c0? GR? GL? etc.
    #2) What is the current invocation of the code table? i.e. is it pointing
    #to G0, G2, G3, G4 invocation?
    #3) What is the designation (active encoding) for the current invocation.
    #e.g. is g0 loaded with 2 byte kanji? or single byte hiragana etc?
    statement = None
    #handle the current character for current encoding
    if is_control_character(b):
      statement = handle_control_character(b, f)
      #possible internal encoding state change via returned control character.
      self.handle_encoding_change(statement)
    elif is_gl_character(b):
      statement = self._GL(b, f)
    elif is_gr_character(b):
      #statement = self._GR(b, f)
      pass

    #TODO: revert the encoding change if it was a non-locking shift

    return statement

  def handle_encoding_change(self, control_code):
    '''Given first character c, read from f and change current
    encoding appropriately
    '''
    pass
    '''
    if control_code is LS0:
      self._GL = self._G0 #LOCKING
    elif control_code is LS1:
      self._GL = self._G1 #LOCKING
    elif control_code is LS2:
      self._GL = self._G2 #LOCKING
    elif control_code is LS3:
      self._GL = self._G3 #LOCKING
    elif control_code is LS1R:
      self._GR = self._G1 #LOCKING
    elif control_code is LS2R:
      self._GR = self._G2 #LOCKING
    elif control_code is LS3R:
      self._GR = self._G3 #LOCKING
    elif control_code is SS2:
      self._GL = self._G2 #SINGLE SHIFT
    elif control_code is SS3:
      self._GL = self._G3 #SINGLE SHIFT  
    elif control_code is ESC:
      #TODO: ARIB STD-B-24 table 7-2 pg 56
      pass
    '''
    
