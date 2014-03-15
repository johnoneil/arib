# vim: set ts=2 expandtab:
'''
Module: code_set.py
Desc: stateful arib teletext decoder
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Sat, March 16th 2014

handling for code sets in japanese closed captions

'''

from arib_exceptions import UnimplimentedError
import read


class Kanji(object):
  '''2 byte kanji code set.
  basically just euc-jisx0213 seven bit encoding.
  We read the initial byte from a binary filestream, it's purpose is
  detected, and that byte (and the stream) passed to this class for
  further reading and decoding.
  so it goes BYTE-->(logic determining type)-->Instance of Kanji class
  Intances of this clas can then be stored, and printed, resulting in 
  a UTF-8 version of the character.
  '''
  FINAL_BYTE = 0x42

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

class Alphanumeric(object):
  FINAL_BYTE = 0x4a
  def __init__(self):
    pass

  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class Hiragana(object):
  FINAL_BYTE = 0x30
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class Katakana(object):
  FINAL_BYTE = 0x31
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class MosaicA(object):
  FINAL_BYTE = 0x32
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class MosaicB(object):
  FINAL_BYTE = 0x33
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class MosaicC(object):
  FINAL_BYTE = 0x34
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class MosaicD(object):
  FINAL_BYTE = 0x35
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class ProportionalAlphanumeric(object):
  FINAL_BYTE = 0x36
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class ProportionalHiragana(object):
  FINAL_BYTE = 0x37
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class ProportionalKatakana(object):
  FINAL_BYTE = 0x38
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class JISX0201Katakana(object):
  FINAL_BYTE = 0x49
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class JISCompatiblePlane1(object):
  FINAL_BYTE = 0x39
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class JISCompatiblePlane2(object):
  FINAL_BYTE = 0x3a
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class AdditionalSymbols(object):
  FINAL_BYTE = 0x3b
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

class Macro(object):
  FINAL_BYTE = 0x70
  def __init__(self):
    pass
  @staticmethod
  def decode(b, f):
    raise UnimplimentedError()

CODE_SET_TABLE = {
  Kanji.FINAL_BYTE : Kanji.decode,
  Alphanumeric.FINAL_BYTE : Alphanumeric.decode,
  Hiragana.FINAL_BYTE : Hiragana.decode,
  Katakana.FINAL_BYTE : Katakana.decode,
  MosaicA.FINAL_BYTE : MosaicA.decode,
  MosaicB.FINAL_BYTE : MosaicB.decode,
  MosaicC.FINAL_BYTE : MosaicC.decode,
  MosaicD.FINAL_BYTE : MosaicD.decode,
  ProportionalAlphanumeric.FINAL_BYTE : ProportionalAlphanumeric.decode,
  ProportionalHiragana.FINAL_BYTE : ProportionalHiragana.decode,
  ProportionalKatakana.FINAL_BYTE : ProportionalKatakana.decode,
  JISX0201Katakana.FINAL_BYTE : JISX0201Katakana .decode,
  JISCompatiblePlane1.FINAL_BYTE : JISCompatiblePlane1.decode,
  JISCompatiblePlane2.FINAL_BYTE : JISCompatiblePlane2.decode,
  AdditionalSymbols.FINAL_BYTE : AdditionalSymbols.decode,
  Macro.FINAL_BYTE : Macro.decode,
}

def code_set_from_final_byte(b):
  '''Given the final byte of a code set control sequence
  return an object representing that code set and its decoding
  '''
  return CODE_SET_TABLE[b]()
  
