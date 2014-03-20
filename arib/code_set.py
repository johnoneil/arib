# -*- coding: utf-8 -*-
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
  We read the initial byte from a binary filestream, its purpose is
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
  def __init__(self,b, f):
    '''Read from stream one byte alphanumeric
    Arib alphanumeric is the same as ASCII, except 
    the '\' backslash has been replaced by　¥.
    In cases of characters not representable by on screen
    characters, decoding error is raised.
    '''
    self._args = []
    self._args.append(b)

    s =''.join('{:02x}'.format(a & 0xef) for a in self._args)
    h = s.decode('hex')
    decoded = h.decode('ascii')
    self._character = 'ASCII ' + decoded.encode('utf-8')
    if self._character == '\\':
      self._character = '¥'

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return self._character


  @staticmethod
  def decode(b, f):
    return Alphanumeric(b, f)


class Hiragana(object):
  FINAL_BYTE = 0x30
  def __init__(self,b, f):
    '''Read from stream one byte hiragana
    '''
    self._args = []
    self._args.append(b)

    upper_byte = (b >> 4) & 0x0e
    lower_byte = b & 0x0f
    #self._character = '{:#x}'.format(self._args[0] & 0xef)
    self._character = Hiragana.CODING[lower_byte][upper_byte]

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return 'One Byte Hiragana ' + self._character

  @staticmethod
  def decode(b, f):
    return Hiragana(b, f)

  #single byte hiragana coding table ARIB STD-B24 table 7-7 pg.50
  CODING = {
    0x0 : {0x2 : ' ', 0x3 : 'ぐ', 0x4 : 'だ', 0x5 : 'ば', 0x6 :'む', 0x7 : 'る',},
    0x1 : {0x2 : 'ぁ', 0x3 : 'け', 0x4 : 'ち', 0x5 : 'ぱ', 0x6 :'め', 0x7 : 'ゑ',},
    0x2 : {0x2 : 'あ', 0x3 : 'げ', 0x4 : 'ぢ', 0x5 : 'ひ', 0x6 :'も', 0x7 : 'を',},
    0x3 : {0x2 : 'ぃ', 0x3 : 'こ', 0x4 : 'っ', 0x5 : 'び', 0x6 :'ゃ', 0x7 : 'ん',},
    0x4 : {0x2 : 'い', 0x3 : 'ご', 0x4 : 'つ', 0x5 : 'ぴ', 0x6 :'や', 0x7 : '　',},
    0x5 : {0x2 : 'ぅ', 0x3 : 'さ', 0x4 : 'づ', 0x5 : 'ふ', 0x6 :'ゅ', 0x7 : '　',},
    0x6 : {0x2 : 'う', 0x3 : 'ざ', 0x4 : 'て', 0x5 : 'ぶ', 0x6 :'ゆ', 0x7 : '　',},
    0x7 : {0x2 : 'ぇ', 0x3 : 'し', 0x4 : 'で', 0x5 : 'ぷ', 0x6 :'ょ', 0x7 : 'ゝ',},
    0x8 : {0x2 : 'え', 0x3 : 'じ', 0x4 : 'と', 0x5 : 'へ', 0x6 :'よ', 0x7 : 'ゞ',},
    0x9 : {0x2 : 'ぉ', 0x3 : 'す', 0x4 : 'ど', 0x5 : 'べ', 0x6 :'ら', 0x7 : 'ー',},
    0xa : {0x2 : 'お', 0x3 : 'ず', 0x4 : 'な', 0x5 : 'ぺ', 0x6 :'り', 0x7 : '。',},
    0xb : {0x2 : 'か', 0x3 : 'せ', 0x4 : 'に', 0x5 : 'ほ', 0x6 :'る', 0x7 : '「',},
    0xc : {0x2 : 'が', 0x3 : 'ぜ', 0x4 : 'ぬ', 0x5 : 'ぼ', 0x6 :'れ', 0x7 : '」',},
    0xd : {0x2 : 'き', 0x3 : 'そ', 0x4 : 'ね', 0x5 : 'ぽ', 0x6 :'ろ', 0x7 : '、',},
    0xe : {0x2 : 'ぎ', 0x3 : 'ぞ', 0x4 : 'の', 0x5 : 'ま', 0x6 :'ゎ', 0x7 : '.',},
    0xf : {0x2 : 'く', 0x3 : 'た', 0x4 : 'は', 0x5 : 'み', 0x6 :'わ', 0x7 : '　',},
  }


class Katakana(object):
  FINAL_BYTE = 0x31
  def __init__(self,b, f):
    '''Read from stream one byte katakana
    '''
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __str__(self):
    '''stringify to utf-8
    '''
    return 'One Byte katakana ' + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return Katakana(b, f)


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
  def __init__(self, b, f):
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
    return Macro(b, f)

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
    print 'init drcs1'
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
    print 'decode DRCS1'
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

def code_set_handler_from_final_byte(b):
  '''Given the final byte of a code set control sequence
  return an object representing that code set and its decoding
  '''
  return CODE_SET_TABLE[b]
  
