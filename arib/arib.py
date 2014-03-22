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


def main():
  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Elementary Stream.')
  parser.add_argument('infile', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  #parser.add_argument('-p', '--pid', help='Pid of stream .', type=str, default='')
  args = parser.parse_args()

  infilename = args.infile
  if not os.path.exists(infilename):
    print 'Please provide input Elemenatry Stream file.'
    os.exit(-1)
    
  for data_group in next_data_group(infilename):
    pass

if __name__ == "__main__":
  main()
