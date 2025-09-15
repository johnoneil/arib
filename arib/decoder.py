# vim: set ts=2 expandtab:
'''
Module: decoder.py
Desc: stateful arib teletext decoder
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Friday, March 15th 2014

'''

from arib import read
from arib.control_characters import is_control_character
from arib.control_characters import handle_control_character
import arib.control_characters as control_char
from arib import code_set
from arib.arib_exceptions import DecodingError

DEBUG = True


class ref(object):
  '''Emulate pointer behavior
  After http://stackoverflow.com/questions/1145722/simulating-pointers-in-python
  '''
  def __init__(self, obj):
    self.obj = obj
  def get(self):
    return self.obj
  def set(self, obj):
    self.obj = obj
  def __call__(self, *args):
    return self.obj(*args)


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
    self._G0 = ref(code_set.Kanji.decode)
    self._G1 = ref(code_set.Katakana.decode)#ref(code_set.Alphanumeric.decode)
    self._G2 = ref(code_set.Hiragana.decode) #code_set.DRCS1.decode
    #self._G2 = ref(code_set.DRCS1.decode)
    self._G3 = ref(code_set.Macro.decode)
    self._single_shift = None

    #default code table 'invocations'
    self._GL = self._G0
    self._GR = self._G2

  def decode(self, f):
    '''Return an object representing the current character
    '''
    b = read.ucb(f)
    if DEBUG:
      print('-->{:02x}'.format(b))
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
    elif is_gl_character(b):
      statement = self._GL(b, f)
    elif is_gr_character(b):
      statement = self._GR(b, f)

    #possible internal encoding state change via returned control character.
    self.handle_encoding_change(statement)

    return statement

  def handle_encoding_change(self, control_code):
    '''Given first character c, read from f and change current
    encoding appropriately
    '''
    #print 'handle_encoding_change'
    #If we have a saved control set hanging around, this means the current
    #was set by SINGLE (NON LOCKING) SHIFT, so revert back to the saved
    if self._single_shift:
      self._GL.set(self._single_shift)
      self._single_shift = None

    #Handle single byte dedicated control codes
    if isinstance(control_code, control_char.LS0):
      if DEBUG:
        print("switching _GL to table G0")
      self._GL = self._G0
      return
    if isinstance(control_code ,control_char.LS1):
      if DEBUG:
        print("switching GL to table G1")
      self._GL = self._G1
      return
    if isinstance(control_code, control_char.SS2):
      #this is a single shift operator, so store the current mapping
      #The stored value will be set back to active after decoding one character
      if DEBUG:
        print("setting table GL to single shift G2")
      self._single_shift = self._GL.get()
      self._GL = self._G2
      return
    if isinstance(control_code, control_char.SS3):
      #this is a single shift operator, so store the current mapping
      #The stored value will be set back to active after decoding one character
      if DEBUG:
        print("setting table GL to single shift GL")
      self._single_shift = self._GL.get()
      self._GL = self._G3
      return
    
    if not isinstance(control_code, control_char.ESC):
     return

    if control_code.is_invocation():
      if DEBUG:
        print("control code invocation.")
      control_code.invoke(self)
      return

    if control_code.is_designation():
      if DEBUG:
        print("control code designation")
      control_code.designate(self)
      return

    raise DecodingError() 
    
  
    
