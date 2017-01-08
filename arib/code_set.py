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

class Gaiji(object):
  #after ARIB std docs pg 54 onwards
  # note that columns and rows are swapped in this table to
  # facilitate reading
  ENCODING = {
    1  : { 90 : u'◻', 91 : u'◻', 92 : u'➡', 93 : u'◻', 94 : u'◻',},
    2  : { 90 : u'◻', 91 : u'◻', 92 : u'⬅', 93 : u'◻', 94 : u'◻',},
    3  : { 90 : u'◻', 91 : u'◻', 92 : u'⬆', 93 : u'◻', 94 : u'◻',},
    4  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    5  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    6  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    7  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    8  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    9  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    10 : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    11  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    12  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    13  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    14  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    15  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    16  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    17  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    18  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    19  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    20  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    21  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    22  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    23  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    24  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    25  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    26  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    27  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    28  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    29  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    30  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    31  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    32  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    33  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    34  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    35  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    36  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    37  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    38  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    39  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    40  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    41  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    42  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    43  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    44  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    45  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    46  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    47  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    48  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    49  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    50  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    51  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    52  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    53  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    54  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    55  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    56  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    57  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    58  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    59  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    60  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    61  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    62  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    63  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    64  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    65  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    66  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    67  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    68  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    69  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    70  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    71  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    72  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    73  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    74  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    75  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    76  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    77  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    78  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'‼', 94 : u'◻',},
    79  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'⁈', 94 : u'◻',},
    80  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    81  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    82  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    83  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    84  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    85  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    86  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    87  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    88  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'*', 94 : u'◻',},
    89  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'*', 94 : u'◻',},
    90  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'♫', 94 : u'◻',},
    91  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'☎', 94 : u'◻',},
    92  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    93  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    94  : { 90 : u'◻', 91 : u'◻', 92 : u'◻', 93 : u'◻', 94 : u'◻',},
    }

  @staticmethod
  def is_gaiji(v):
    row = v[0]&0x7f-0x20
    col = v[1] & 0x007f - 0x20
    return  (row >= 90 and row <= 94) and (col >=1 and col <= 94)

  @staticmethod
  def decode(v):
    #[124][33]--> 0b01111100, 0b00100001
    #(0x7c-0x20)(0x21-0x20)--> 0x5c, 0x1 --> 92(col), 1(row)
    #upper byte can be used to calculate row
    row = v[0]&0x7f-0x20
    col = v[1]&0x007f-0x20
    #print 'gaiji-->{r},{c},'.format(r=row, c=col)
    return Gaiji.ENCODING[col][row]


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

    if Gaiji.is_gaiji(self._args):
      #character is outside the shif-jis code set
      self._character = Gaiji.decode(self._args)
    else:
      #form utf-8 encoding of character
      s = u''.join(u'{:02x}'.format(a|0x80) for a in self._args)
      h = s.decode('hex')
      try:
          self._character = h.decode('euc-jisx0213')
      except:
          self._character = u'◻'
    #print(u'{code}-->{char}'.format(code=str(self._args), char=self._character).encode('utf-8'))

  def __len__(self):
    return len(self._args)

  def __unicode__(self):
    '''stringify
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

    s =''.join('{:02x}'.format(a) for a in self._args)
    h = s.decode('hex')
    self._character = h.decode('ascii')
    if self._character == u'\\':
      self._character = u'¥'

  def __len__(self):
    return len(self._args)

  def __unicode__(self):
    '''stringify
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

    upper_nibble = (b >> 4) & 0x07
    lower_nibble = b & 0x0f
    self._character = Hiragana.ENCODING[lower_nibble][upper_nibble]

  def __len__(self):
    return len(self._args)

  def __unicode__(self):
    '''stringify
    '''
    return self._character

  @staticmethod
  def decode(b, f):
    return Hiragana(b, f)

  #single byte hiragana coding table ARIB STD-B24 table 7-7 pg.50
  ENCODING = {
    0x0 : {0x2 : u' ', 0x3 : u'ぐ', 0x4 : u'だ', 0x5 : u'ば', 0x6 : u'む', 0x7 : u'る',},
    0x1 : {0x2 : u'ぁ', 0x3 : u'け', 0x4 : u'ち', 0x5 : u'ぱ', 0x6 : u'め', 0x7 : u'ゑ',},
    0x2 : {0x2 : u'あ', 0x3 : u'げ', 0x4 : u'ぢ', 0x5 : u'ひ', 0x6 : u'も', 0x7 : u'を',},
    0x3 : {0x2 : u'ぃ', 0x3 : u'こ', 0x4 : u'っ', 0x5 : u'び', 0x6 : u'ゃ', 0x7 : u'ん',},
    0x4 : {0x2 : u'い', 0x3 : u'ご', 0x4 : u'つ', 0x5 : u'ぴ', 0x6 : u'や', 0x7 : u'　',},
    0x5 : {0x2 : u'ぅ', 0x3 : u'さ', 0x4 : u'づ', 0x5 : u'ふ', 0x6 : u'ゅ', 0x7 : u'　',},
    0x6 : {0x2 : u'う', 0x3 : u'ざ', 0x4 : u'て', 0x5 : u'ぶ', 0x6 : u'ゆ', 0x7 : u'　',},
    0x7 : {0x2 : u'ぇ', 0x3 : u'し', 0x4 : u'で', 0x5 : u'ぷ', 0x6 : u'ょ', 0x7 : u'ゝ',},
    0x8 : {0x2 : u'え', 0x3 : u'じ', 0x4 : u'と', 0x5 : u'へ', 0x6 : u'よ', 0x7 : u'ゞ',},
    0x9 : {0x2 : u'ぉ', 0x3 : u'す', 0x4 : u'ど', 0x5 : u'べ', 0x6 : u'ら', 0x7 : u'ー',},
    0xa : {0x2 : u'お', 0x3 : u'ず', 0x4 : u'な', 0x5 : u'ぺ', 0x6 : u'り', 0x7 : u'。',},
    0xb : {0x2 : u'か', 0x3 : u'せ', 0x4 : u'に', 0x5 : u'ほ', 0x6 : u'る', 0x7 : u'「',},
    0xc : {0x2 : u'が', 0x3 : u'ぜ', 0x4 : u'ぬ', 0x5 : u'ぼ', 0x6 : u'れ', 0x7 : u'」',},
    0xd : {0x2 : u'き', 0x3 : u'そ', 0x4 : u'ね', 0x5 : u'ぽ', 0x6 : u'ろ', 0x7 : u'、',},
    0xe : {0x2 : u'ぎ', 0x3 : u'ぞ', 0x4 : u'の', 0x5 : u'ま', 0x6 : u'ゎ', 0x7 : u'・',},
    0xf : {0x2 : u'く', 0x3 : u'た', 0x4 : u'は', 0x5 : u'み', 0x6 : u'わ', 0x7 : u'　',},
  }


class Katakana(object):
  FINAL_BYTE = 0x31
  def __init__(self,b, f):
    '''Read from stream one byte katakana
    '''
    self._args = []
    self._args.append(b)

    upper_nibble = (b >> 4) & 0x07
    lower_nibble = b & 0x0f
    self._character = Katakana.ENCODING[lower_nibble][upper_nibble]

  def __len__(self):
    return len(self._args)

  def __unicode__(self):
    '''stringify
    '''
    return self._character

  @staticmethod
  def decode(b, f):
    return Katakana(b, f)

  #single byte katakana coding table ARIB STD-B24 table 7-6 pg.49
  ENCODING = {
    0x0 : {0x2 : u' ', 0x3 : u'グ', 0x4 : u'ダ', 0x5 : u'バ', 0x6 : u'ム', 0x7 : u'ヰ',},
    0x1 : {0x2 : u'ァ', 0x3 : u'ケ', 0x4 : u'チ', 0x5 : u'パ', 0x6 : u'メ', 0x7 : u'ヱ',},
    0x2 : {0x2 : u'ア', 0x3 : u'ゲ', 0x4 : u'ジ', 0x5 : u'ヒ', 0x6 : u'モ', 0x7 : u'ヲ',},
    0x3 : {0x2 : u'ィ', 0x3 : u'コ', 0x4 : u'ッ', 0x5 : u'ビ', 0x6 : u'ャ', 0x7 : u'ン',},
    0x4 : {0x2 : u'イ', 0x3 : u'ゴ', 0x4 : u'ツ', 0x5 : u'ピ', 0x6 : u'ヤ', 0x7 : u'ヴ',},
    0x5 : {0x2 : u'ゥ', 0x3 : u'サ', 0x4 : u'づ', 0x5 : u'フ', 0x6 : u'ュ', 0x7 : u'ヵ',},
    0x6 : {0x2 : u'ウ', 0x3 : u'ザ', 0x4 : u'テ', 0x5 : u'ブ', 0x6 : u'ユ', 0x7 : u'ヶ',},
    0x7 : {0x2 : u'ェ', 0x3 : u'シ', 0x4 : u'デ', 0x5 : u'プ', 0x6 : u'ョ', 0x7 : u'ヽ',},
    0x8 : {0x2 : u'エ', 0x3 : u'ジ', 0x4 : u'ト', 0x5 : u'ヘ', 0x6 : u'ヨ', 0x7 : u'ヾ',},
    0x9 : {0x2 : u'ォ', 0x3 : u'ス', 0x4 : u'ド', 0x5 : u'ベ', 0x6 : u'ラ', 0x7 : u'ー',},
    0xa : {0x2 : u'オ', 0x3 : u'ズ', 0x4 : u'ナ', 0x5 : u'ペ', 0x6 : u'リ', 0x7 : u'。',},
    0xb : {0x2 : u'カ', 0x3 : u'セ', 0x4 : u'ニ', 0x5 : u'ホ', 0x6 : u'ル', 0x7 : u'「',},
    0xc : {0x2 : u'ガ', 0x3 : u'ゼ', 0x4 : u'ヌ', 0x5 : u'ボ', 0x6 : u'レ', 0x7 : u'」',},
    0xd : {0x2 : u'キ', 0x3 : u'ソ', 0x4 : u'ネ', 0x5 : u'ポ', 0x6 : u'ロ', 0x7 : u'、',},
    0xe : {0x2 : u'ギ', 0x3 : u'ゾ', 0x4 : u'ノ', 0x5 : u'マ', 0x6 : u'ヮ', 0x7 : u'・',},
    0xf : {0x2 : u'ク', 0x3 : u'タ', 0x4 : u'ハ', 0x5 : u'ミ', 0x6 : u'ワ', 0x7 : u'　',},
  }


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

  def __unicode__(self):
    '''stringify
    '''
    return u'{n} {s}'.format(n=self.__class__.__name__, s=u' '.join('{:#x}'.format(x) for x in self._args))

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

  def __unicode__(self):
    '''stringify
    '''
    return u'{n} {s}'.format(n=unicode(self.__class__.__name__), s=u' '.join('{:#x}'.format(x) for x in self._args))
    #return self.__class__.__name__ + ' '.join('{:#x}'.format(x) for x in self._args)

  @staticmethod
  def decode(b, f):
    return DRCS0(b, f)

class DRCS1(object):
  FINAL_BYTE = 0x41
  def __init__(self,b, f):
    #print 'init drcs1'
    self._args = []
    self._args.append(b)

  def __len__(self):
    return len(self._args)

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify to
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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

  def __unicode__(self):
    '''stringify
    '''
    return u'◻'

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
  #DRCS2.FINAL_BYTE : DRCS2.decode,#TODO: fix final byte key overlap with non-DRCS
  DRCS3.FINAL_BYTE : DRCS3.decode,
  DRCS4.FINAL_BYTE : DRCS4.decode,
  DRCS5.FINAL_BYTE : DRCS5.decode,
  DRCS6.FINAL_BYTE : DRCS6.decode,
  DRCS7.FINAL_BYTE : DRCS7.decode,
  DRCS8.FINAL_BYTE : DRCS8.decode,
  DRCS9.FINAL_BYTE : DRCS9.decode,
  #DRCS10.FINAL_BYTE : DRCS10.decode,#TODO: fix final byte key overlap with non-DRCS
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
