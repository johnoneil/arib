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

class DRCS0(object):
  '''0 is the 2 byte DRCS encoding
  '''
  FINAL_BYTE = 0x40
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)
    self._args.append(read.ucb(f))

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS0(b, f)

class DRCS1(object):
  FINAL_BYTE = 0x41
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS1(b, f)

class DRCS2(object):
  FINAL_BYTE = 0x42
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS2(b, f)

class DRCS3(object):
  FINAL_BYTE = 0x43
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS3(b, f)

class DRCS4(object):
  FINAL_BYTE = 0x44
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS4(b, f)

class DRCS5(object):
  FINAL_BYTE = 0x45
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS5(b, f)

class DRCS6(object):
  FINAL_BYTE = 0x46
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS6(b, f)

class DRCS7(object):
  FINAL_BYTE = 0x47
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS7(b, f)

class DRCS8(object):
  FINAL_BYTE = 0x48
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS8(b, f)

class DRCS9(object):
  FINAL_BYTE = 0x49
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS9(b, f)

class DRCS10(object):
  FINAL_BYTE = 0x4a
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS10(b, f)

class DRCS11(object):
  FINAL_BYTE = 0x4b
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS11(b, f)

class DRCS12(object):
  FINAL_BYTE = 0x4c
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS12(b, f)

class DRCS13(object):
  FINAL_BYTE = 0x4d
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS13(b, f)

class DRCS14(object):
  FINAL_BYTE = 0x4e
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS14(b, f)

class DRCS15(object):
  FINAL_BYTE = 0x4f
  def __init__(self,b, f):
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS15(b, f)

#ARIB STD-B24 Table 7-3 Classification of code set and Final Byte (pg.57)
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
  DRCS0.FINAL_BYTE : DRCS0.decode,
  DRCS1.FINAL_BYTE : DRCS1.decode,
  DRCS2.FINAL_BYTE : DRCS2.decode,
  DRCS3.FINAL_BYTE : DRCS3.decode,
  DRCS4.FINAL_BYTE : DRCS4.decode,
  DRCS5.FINAL_BYTE : DRCS5.decode,
  DRCS6.FINAL_BYTE : DRCS6.decode,
  DRCS7.FINAL_BYTE : DRCS7.decode,
  DRCS8.FINAL_BYTE : DRCS8.decode,
  DRCS9.FINAL_BYTE : DRCS9.decode,
  DRCS10.FINAL_BYTE : DRCS10.decode,
  DRCS11.FINAL_BYTE : DRCS11.decode,
  DRCS12.FINAL_BYTE : DRCS12.decode,
  DRCS13.FINAL_BYTE : DRCS13.decode,
  DRCS14.FINAL_BYTE : DRCS14.decode,
  DRCS15.FINAL_BYTE : DRCS15.decode,
  }

def in_code_set_table(b):
  '''Is this in the code table
  '''
  return b in CODE_SET_TABLE

def code_set_from_final_byte(b, f):
  '''Given the final byte of a code set control sequence
  return an object representing that code set and its decoding
  '''
  return CODE_SET_TABLE[b](b, f)
  
