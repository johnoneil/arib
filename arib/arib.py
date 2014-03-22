#!/usr/bin/env python 
# vim: set ts=2 expandtab:
'''
Module:arib.py
Desc: parsing Closed Captions from Japanese transport/elementary streams
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

  
'''
import os
import argparse
from data_group import next_data_group
from closed_caption import next_data_unit
from closed_caption import StatementBody
import code_set

def formatter(statements):
  '''Turn a list of decoded closed caption statements
    into something we want (probably just plain text)
  '''
  line = ''
  for s in statements:
    if isinstance(s, code_set.Kanji) or isinstance(s, code_set.Alphanumeric) \
      or isinstance(s, code_set.Hiragana) or isinstance(s, code_set.Katakana):
      line += str(s)

  return line


def main():
  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Elementary Stream.')
  parser.add_argument('infile', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  #parser.add_argument('-p', '--pid', help='Pid of stream .', type=str, default='')
  args = parser.parse_args()

  infilename = args.infile
  if not os.path.exists(infilename):
    print 'Please provide input Elemenatry Stream file.'
    os.exit(-1)
  
  #go through the file, taking packets apart as we go
  for data_group in next_data_group(infilename):
    #if this isn't management data it must have caption data
    if not data_group.is_management_data():
      #take the caption data apart
      caption = data_group.payload()
      for data_unit in next_data_unit(caption):
        if not isinstance(data_unit.payload(), StatementBody):
          continue
        print formatter(data_unit.payload().payload())
        

if __name__ == "__main__":
  main()
