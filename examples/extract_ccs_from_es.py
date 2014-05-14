#!/usr/bin/env python 
# vim: set ts=2 expandtab:
'''
Module:arib.py
Desc: Example xtracting Japanese ARIB std B-24 CC data from an MPEG PES fille
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014
updated: Tuesday, May 13th 2014
  
'''
import os
import argparse
from arib.data_group import next_data_group
from arib.closed_caption import next_data_unit
from arib.closed_caption import StatementBody
import arib.code_set as code_set
import arib.control_characters as control_characters


DISPLAYED_CC_STATEMENTS = [
  code_set.Kanji,
  code_set.Alphanumeric,
  code_set.Hiragana,
  code_set.Katakana,
  control_characters.APS,
  control_characters.MSZ,
  control_characters.NSZ,
  control_characters.SP,
  control_characters.SSZ,
  control_characters.CS,
  control_characters.CSI,
]

def formatter(statements):
  '''Turn a list of decoded closed caption statements
    into something we want (probably just plain text)
  '''
  line = ''
  #for s in statements:
  #  print(str(type(s)))
  for s in statements:
    if type(s) in DISPLAYED_CC_STATEMENTS:
      line += str(s)
    else:
      print(str(type(s)))

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
  
  #ARIB data is packed into a PES at a high level as 'Data Group' structures
  #We iterate through the input PES file via the next_data_group generator
  for data_group in next_data_group(infilename):
    #There are several types of Data Groups. I'm here filtering out those
    #that are 'management data' to get to those which contain basic CC text.
    if not data_group.is_management_data():
      #We now have a Data Group that contains caption data.
      #We take out its payload, but this is further divided into 'Data Unit' structures
      caption = data_group.payload()
      #iterate through the Data Units in this payload via another generator.
      for data_unit in next_data_unit(caption):
        #we're only interested in those Data Units which are "statement body" to get CC data.
        if not isinstance(data_unit.payload(), StatementBody):
          continue
        #okay. Finally we've got a data unit with CC data. Feed its payload to the custom
        #formatter function above. This dumps the basic text to stdout.
        line = formatter(data_unit.payload().payload())
        if len(line):
          print(line)
        

if __name__ == "__main__":
  main()
