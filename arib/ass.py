# vim: set ts=2 expandtab:
# -*- coding: utf-8 -*-
'''
Module: ass.py
Desc: Advanced SubStation Alpha subtitle file formatter
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

This module provides a formatter class that can be used
to turn arib package subtitle objects into a .ass 
file.
  
'''

import arib.code_set as code_set
import arib.control_characters as control_characters
import codecs
import re

class Pos(object):
  '''Screen position in pixels
  '''
  def __init__(self, x, y):
    self._x = x
    self._y = y

  @property
  def x(self):
    return self._x

  @property
  def y(self):
    return self._y


class Size(object):
  '''Screen width, height of an area in pixels
  '''
  def __init__(self, w, h):
    self._w = w
    self._h = h

  @property
  def width(self):
    return self._w

  @property
  def height(self):
    return self._h


class ClosedCaptionArea(object):
  def __init__(self):
    self._UL = Pos(170, 30)
    self._Dimensions = Size(620, 480)
    self._CharacterDim = Size(36, 36)
    self._char_spacing = 4
    self._line_spacing = 24

  @property
  def UL(self):
    return self._UL

  @property
  def Dimensions(self):
    return self._Dimensions

  def RowCol2ScreenPos(self, row, col):
    # issue #13. Active Position Set values seem incorrect.
    # It doesn't jive with any documentation i've read but the APS values coming
    # out of some .ts files (specifically aijin) seem incorrect by a factor of 2.
    # According to text area data, there should be 8 text lines in the CC area but
    # values for CC APS values are 12-15.
    # I'm assuming (again with no documentation justification) that these values
    # are meant to provide sub-line positioning data, so we'll scale the APS data by 0.5
    # allowing positioning at, say, the 6.5th text line rather than just integer value lines.
    r = float(row)/2.0
    c = float(col)/2.0
    return Pos(self.UL.x + c * (self._CharacterDim.width + self._char_spacing), self.UL.y + r * (self._CharacterDim.height + self._line_spacing))

class ASSFile(object):
  '''Wrapper for a single open utf-8 encoded .ass subtitle file
  '''
  def __init__(self, filepath):
    self._f = codecs.open(filepath,'w',encoding='utf8')

  def __del__(self):
    if self._f:
      self._f.close()

  def write(self, line):
    '''Write indicated string to file. usually a line of dialog.
    '''
    self._f.write(line)

  def write_header(self, width, height, title):
    header = u'''[Script Info]
; *****************************************************************************
; File generated via arib-ts2ass
; https://github.com/johnoneil/arib
; *****************************************************************************
Title: Japanese Closed Caption Subtitlies
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
Video Aspect Ratio: 0
Video Zoom: 1
Video Position: 0
Last Style Storage: Default
Video File: {title}


'''.format(width=width, height=height, title=title)
    self._f.write(header)

  def write_styles(self):
    styles = u'''[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: normal,MS UI Gothic,37,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,100,100,0,0,1,2,2,1,10,10,10,0
Style: medium,MS UI Gothic,37,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,50,100,0,0,1,2,2,1,10,10,10,0
Style: small,MS UI Gothic,18,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,100,100,0,0,1,2,2,1,10,10,10,0


'''
    self._f.write(styles)

def asstime(seconds):
  '''format floating point seconds elapsed time to 0:02:14.53
  '''
  days = int(seconds / 86400)
  seconds -= 86400*days
  hrs = int(seconds / 3600)
  seconds -= 3600*hrs
  mins = int(seconds / 60)
  seconds -= 60*mins
  return u'{h:01d}:{m:02d}:{s:02.2f}'.format(h=hrs, m=mins, s=seconds)


def kanji(formatter, k, timestamp):
  formatter._current_lines[-1] += unicode(k)
  #print formatter._current_line.encode('utf-8')

def alphanumeric(formatter, a, timestamp):
  formatter._current_lines[-1] += unicode(a)
  #print formatter._current_line.encode('utf-8')

def hiragana(formatter, h, timestamp):
  formatter._current_lines[-1] += unicode(h)
  #print formatter._current_line.encode('utf-8')

def katakana(formatter, k, timestamp):
  formatter._current_lines[-1] += unicode(k)
  #print formatter._current_line.encode('utf-8')

def medium(formatter, k, timestamp):
  formatter._current_lines[-1] += u'{\\rmedium}' + formatter._current_color
  formatter._current_style = 'medium'

def normal(formatter, k, timestamp):
  formatter._current_lines[-1] += u'{\\rnormal}' + formatter._current_color
  formatter._current_style = 'normal'

def small(formatter, k, timestamp):
  formatter._current_lines[-1] += u'{\\rsmall}' + formatter._current_color
  formatter._current_style = 'small'

def space(formatter, k, timestamp):
  formatter._current_lines[-1] += u' '

def drcs(formatter, c, timestamp):
  formatter._current_lines[-1] += unicode(c)

def black(formatter, k, timestamp):
  #{\c&H000000&} \c&H<bb><gg><rr>& {\c&Hffffff&}
  formatter._current_lines[-1] += u'{\c&H000000&}'
  formatter._current_color = '{\c&H000000&}'

def red(formatter, k, timestamp):
  #{\c&H0000ff&}
  formatter._current_lines[-1] += u'{\c&H0000ff&}'
  formatter._current_color = '{\c&H0000ff&}'
def green(formatter, k, timestamp):
  #{\c&H00ff00&}
  formatter._current_lines[-1] += u'{\c&H00ff00&}'
  formatter._current_color = '{\c&H00ff00&}'

def yellow(formatter, k, timestamp):
  #{\c&H00ffff&}
  formatter._current_lines[-1] += u'{\c&H00ffff&}'
  formatter._current_color = '{\c&H00ffff&}'
def blue(formatter, k, timestamp):
  #{\c&Hff0000&}
  formatter._current_lines[-1] += u'{\c&Hff0000&}'
  formatter._current_color = '{\c&Hff0000&}'
def magenta(formatter, k, timestamp):
  #{\c&Hff00ff&}
  formatter._current_lines[-1] += u'{\c&Hff00ff&}'
  formatter._current_color = '{\c&Hff00ff&}'
def cyan(formatter, k, timestamp):
  #{\c&Hffff00&}
  formatter._current_lines[-1] += u'{\c&Hffff00&}'
  formatter._current_color = '{\c&Hffff00&}'
def white(formatter, k, timestamp):
  #{\c&Hffffff&}
  formatter._current_lines[-1] += u'{\c&Hffffff&}'
  formatter._current_color = '{\c&Hffffff&}'

def position_set(formatter, p, timestamp):
  '''Active Position set coordinates are given in character row, colum
  So we have to calculate pixel coordinates (and then sale them)
  '''
  pos = formatter._CCArea.RowCol2ScreenPos(p.row, p.col)
  line = u'{{\\r{style}}}{color}{{\pos({x},{y})}}'.format(color=formatter._current_color, style=formatter._current_style, x=pos.x, y=pos.y)
  formatter._current_lines.append(line)

a_regex = ur'<CS:"(?P<x>\d{1,4});(?P<y>\d{1,4}) a">'

def control_character(formatter, csi, timestamp):
  '''This will be the most difficult to format, since the same class here
  can represent so many different commands.
  e.g:
  <CS:"7 S"><CS:"170;30 _"><CS:"620;480 V"><CS:"36;36 W"><CS:"4 X"><CS:"24 Y"><Small Text><CS:"170;389 a">
  '''
  cmd = unicode(csi)
  a_match = re.search(a_regex, cmd)
  if a_match:
    x = a_match.group('x')
    y = a_match.group('y')
    formatter._current_lines.append(u'{{\\r{style}}}{color}{{\pos({x},{y})}}'.format(color=formatter._current_color, style=formatter._current_style, x=x, y=y))
    return

pos_regex = ur'({\\pos\(\d{1,4},\d{1,4}\)})'

def clear_screen(formatter, cs, timestamp):

  if(timestamp - formatter._elapsed_time_s > formatter._tmax):
    end_time = asstime(formatter._elapsed_time_s + formatter._tmax)
  else:
    end_time = asstime(timestamp)
  start_time = asstime(formatter._elapsed_time_s)

  if (len(formatter._current_lines[0]) or len(formatter._current_lines)) and start_time != end_time:
    for l in reversed(formatter._current_lines):
      if not len(l):
        continue
     
      line = u'Dialogue: 0,{start_time},{end_time},normal,,0000,0000,0000,,{line}\\N\n'.format(start_time=start_time, end_time=end_time, line=l)
      #TODO: add option to dump to stdout
      #print line.encode('utf-8')
      formatter._ass_file.write(line)
      formatter._current_lines = [u'']

  formatter._elapsed_time_s = timestamp
  

class ASSFormatter(object):
  '''
  Format ARIB objects to dialog of the sort below:
  Dialogue: 0,0:02:24.54,0:02:30.55,small,,0000,0000,0000,,{\pos(500,900)}ゴッド\N
  Dialogue: 0,0:02:24.54,0:02:30.55,small,,0000,0000,0000,,{\pos(780,900)}ほかく\N
  Dialogue: 0,0:02:24.54,0:02:30.55,normal,,0000,0000,0000,,{\pos(420,1020)}ＧＯＤの捕獲を目指す・\N
  '''

  DISPLAYED_CC_STATEMENTS = {
    code_set.Kanji : kanji,
    code_set.Alphanumeric : alphanumeric,
    code_set.Hiragana : hiragana,
    code_set.Katakana : katakana,
    control_characters.APS : position_set,#{\pos(<X>,<Y>)}
    control_characters.MSZ : medium, #{\rmedium}
    control_characters.NSZ : normal, #{\rnormal}
    control_characters.SP : space, #' '
    control_characters.SSZ : small, #{\rsmall}
    control_characters.CS : clear_screen,
    control_characters.CSI : control_character, #{\pos(<X>,<Y>)}
    #control_characters.COL,
    control_characters.BKF : black,#{\c&H000000&} \c&H<bb><gg><rr>&
    control_characters.RDF : red,#{\c&H0000ff&}
    control_characters.GRF : green,#{\c&H00ff00&}
    control_characters.YLF : yellow,#{\c&H00ffff&}
    control_characters.BLF : blue,#{\c&Hff0000&}
    control_characters.MGF : magenta,#{\c&Hff00ff&}
    control_characters.CNF : cyan,#{\c&Hffff00&}
    control_characters.WHF : white,#{\c&Hffffff&}

    #largely unhandled DRCS just replaces them with unicode unknown character square
    code_set.DRCS0 : drcs,
    code_set.DRCS1 : drcs,
    code_set.DRCS2 : drcs,
    code_set.DRCS3 : drcs,
    code_set.DRCS4 : drcs,
    code_set.DRCS5 : drcs,
    code_set.DRCS6 : drcs,
    code_set.DRCS7 : drcs,
    code_set.DRCS8 : drcs,
    code_set.DRCS9 : drcs,
    code_set.DRCS10 : drcs,
    code_set.DRCS11 : drcs,
    code_set.DRCS12 : drcs,
    code_set.DRCS13 : drcs,
    code_set.DRCS14 : drcs,
    code_set.DRCS15 : drcs,

  }


  def __init__(self, ass_file=None, default_color='white', tmax=5, width=960, height=540, video_filename='unknown'):
    '''
    :param width: width of target screen in pixels
    :param height: height of target screen in pixels
    :param format_callback: callback method of form <None>callback(string) that
    can be used to dump strings to file upon each subsequent "clear screen" command.
    '''
    self._color = default_color
    self._tmax = tmax
    self._CCArea = ClosedCaptionArea()
    self._pos = Pos(0, 0)
    self._elapsed_time_s = 0.0
    self._ass_file = ass_file or ASSFile(u'./output.ass')
    self._ass_file.write_header(width,height, video_filename.decode("utf-8"))
    self._ass_file.write_styles()
    self._current_lines = [u'']
    self._current_style = 'normal'
    self._current_color = '{\c&Hffffff&}'

  def format(self, captions, timestamp):
    '''Format ARIB closed caption info tinto text for an .ASS file
    '''
    #TODO: Show progress in some way
    #print('File elapsed time seconds: {s}'.format(s=timestamp))
    #line = u'{t}: {l}\n'.format(t=timestamp, l=u''.join([unicode(s) for s in captions if type(s) in ASSFormatter.DISPLAYED_CC_STATEMENTS]))
    
    for c in captions:
      if type(c) in ASSFormatter.DISPLAYED_CC_STATEMENTS:
        #invoke the handler for this object type
        ASSFormatter.DISPLAYED_CC_STATEMENTS[type(c)](self, c, timestamp)
      else:
        #TODO: Warning of unhandled characters
        pass
        #print str(type(c))
