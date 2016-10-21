#!/usr/bin/env python
'''
Module: test
Desc: Test to see how quickly I can parse TS es packets
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, October 20th 2016

'''
import os
import sys
import argparse

PACKET_SIZE = 188
SYNC_BYTE = 'G'

#generator
def next_packet(filename):
  with open(filename, 'rb') as f:
    while True:
      packet = f.read(PACKET_SIZE)
      if packet:
        # first byte SHOULD be the sync byte
        # but if it isn't find one.
        if packet[0] != SYNC_BYTE:
          start_byte = 0
          print packet[0]
          for i in range(start_byte, PACKET_SIZE):
            if packet[i] == SYNC_BYTE:
              start_byte = i
              break
          # didn't find a new start? FAIL
          if start_byte == 0:
            #print ":".join("{:02x}".format(ord(c)) for c in packet)
            raise Exception("failure to find sync byte in ts packet size.")
            continue
          remainder = f.read(PACKET_SIZE - start_byte)
          packet = packet[start_byte:] + remainder
        yield packet
      else:
        break

def main():
  parser = argparse.ArgumentParser(description='Remove ARIB formatted Closed Caption information from an MPEG TS file and format the results as a standard .ass subtitle file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Transport Stream File)', type=str)
  args = parser.parse_args()

  infilename = args.infile

  if not os.path.exists(infilename):
    print 'Input filename :' + infilename + " does not exist."
    os.exit(-1)

  total_filesize = os.path.getsize(infilename)
  read_size = 0
  percent_read = 0
  prev_percent_read = percent_read

  #CC data is not, in itself timestamped, so we've got to use packet info
  #to reconstruct the timing of the closed captions (i.e. how many seconds into
  #the file are they shown?)
  #show initial progress information
  sys.stdout.write("progress: %d%%   \r" % (percent_read) )
  sys.stdout.flush()
  

  for packet in next_packet(infilename):
    read_size += PACKET_SIZE
    percent_read =((read_size/float(total_filesize))* 100)
    new_percent_read = int(percent_read * 100)
    if new_percent_read != prev_percent_read:
      prev_percent_read = new_percent_read
      sys.stdout.write("progress: %.2f%%   \r" % (percent_read) )
      sys.stdout.flush()
    
if __name__ == "__main__":
  main()
