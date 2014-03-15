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

class Kanji(object):
  '''2 byte kanji. basically just euc-jisx0213 seven bit encoding.
  We read the initial byte from a binary filestream, it's purpose is
  detected, and that byte (and the stream) passed to this class for
  further reading and decoding.
  so it goes BYTE-->(logic determining type)-->Instance of Kanji class
  Intances of this clas can then be stored, and printed, resulting in 
  a UTF-8 version of the character.
  '''
  def __init__(self,b, f):
    '''Read from stream two bytes
    :param b: initial byte value read
    :b type: int
    :param f: filestream we're reading from
    :f type: file stream open for binary reading
    '''
    #read the second byte of the 2 byte kanji
    b2 = read.ucb(f)
    self._args = []
    self._args.append(b)
    self._args.append(b2)

    #form utf-8 encoding of character
    s =''.join('{:02x}'.format(a|0x80) for a in self._args)
    h = s.decode('hex')
    decoded = h.decode('euc-jisx0213')
    self._character = decoded.encode('utf-8')

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self._character

  @staticmethod
  def decode(b, f):
    return Kanji(b, f)

class KanjiDecoder(object):
  '''Wrapper for Kanji encoding so i can
    store its static methods as objects
    i.e. store as 'KanjiDecoder()' rather than Kanji.decode
  '''
  def __init__(self):
    pass
  def decode(self, b, f):
    #invoke the static method on the Kanji class
    return Kanji.decode(b, f)

class Alphanumeric(object):
  FinalByte = 0x4a
  def __init__(self):
    pass

  def decode(self,b, f):
    return Kanji(b, f)

class Hiragana(object):
  FinalByte = 0x30
  def __init__(self):
    pass

  def decode(self, f):
    pass

class Katakana(object):
  FinalByte = 0x31
  def __init__(self):
    pass

  def decode(self, f):
    pass

class MosaicA(object):
  FinalByte = 0x32
  def __init__(self):
    pass

  def decode(self, f):
    pass

class MosaicB(object):
  FinalByte = 0x33
  def __init__(self):
    pass

  def decode(self, f):
    pass

class MosaicC(object):
  FinalByte = 0x34
  def __init__(self):
    pass

  def decode(self, f):
    pass

class MosaicD(object):
  FinalByte = 0x35
  def __init__(self):
    pass

  def decode(self, f):
    pass

class ProportionalAlphanumeric(object):
  FinalByte = 0x36
  def __init__(self):
    pass

  def decode(self, f):
    pass

class ProportionalHiragana(object):
  FinalByte = 0x37
  def __init__(self):
    pass

  def decode(self, f):
    pass

class ProportionalKatakana(object):
  FinalByte = 0x38
  def __init__(self):
    pass

  def decode(self, f):
    pass

class JISX0201Katakana(object):
  FinalByte = 0x49
  def __init__(self):
    pass

  def decode(self, f):
    pass

class JISCompatiblePlane1(object):
  FinalByte = 0x39
  def __init__(self):
    pass

  def decode(self, f):
    pass

class JISCompatiblePlane2(object):
  FinalByte = 0x3a
  def __init__(self):
    pass

  def decode(self, f):
    pass

class AdditionalSymbols(object):
  FinalByte = 0x3b
  def __init__(self):
    pass

  def decode(self, f):
    pass

class Macro(object):
  FinalByte = 0x70
  def __init__(self):
    pass

  def decode(self, f):
    pass
  

class Decoder(object):
  '''Decode a stream of bytes into an array
  of classes representing a decoded teletext packet payload
  '''
  def __init__(self):
    '''Init decoding of code table areas to defaults
    '''
    #default encoding 'designations'
    self._G0 = KanjiDecoder()
    #self._G1 = Alphanumeric
    #self._G2 = Hiragana
    #self._G3 = Macro

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
      statement = self._GL.decode(b, f)
    elif is_gr_character(b):
      #statement = self._GR.decode(b, f)
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
    
