# vim: set ts=2 expandtab:
'''
Module: exceptions.py
Desc: stateful arib teletext decoder
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Sat, March 16th 2014

handling for code sets in japanese closed captions

'''
class UnimplimentedError(Exception):
  def __init__(self, msg='No further info'):
    self._msg = msg
  def __str__(self):
    return 'Unimplimented: {msg}'.format(msg=self._msg)

class DecodingError(Exception):
  def __init__(self, msg='No further info'):
    self._msg = msg
  def __str__(self):
    return 'Decoding Error: {msg}'.format(msg=self._msg)

class FileOpenError(Exception):
  def __init__(self, msg='No further info'):
    self._msg = msg

  def __str__(self):
    return 'File open error: : {msg}'.format(msg=self._msg)

