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
import copy
from arib.data_group import next_data_group
from arib.closed_caption import next_data_unit
from arib.closed_caption import StatementBody
import arib.code_set as code_set
import arib.control_characters as control_characters
from arib.ts import next_ts_packet
from arib.ts import next_pes_packet
from arib.ts import PESPacket
from arib.data_group import DataGroup


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
  #control_characters.COL,
  control_characters.BKF,
  control_characters.RDF,
  control_characters.GRF,
  control_characters.YLF,
  control_characters.BLF,
  control_characters.MGF,
  control_characters.CNF,
  control_characters.WHF,
  #control_characters.TIME,
]

def formatter(statements):
  '''Turn a list of decoded closed caption statements
    into something we want (probably just plain text)
    Note we deal with unicode only here.
  '''
  line = u''.join([unicode(s) for s in statements if type(s) in DISPLAYED_CC_STATEMENTS])
  return line

def main():
  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Elementary Stream.')
  parser.add_argument('infile', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  parser.add_argument('pid', help='Pid of closed caption ES to extract from stream.', type=int)
  args = parser.parse_args()

  pid = args.pid
  infilename = args.infile
  if not os.path.exists(infilename):
    print 'Please provide input Elemenatry Stream file.'
    os.exit(-1)

  #CC data is not, in itself timestamped, so we've got to use packet info
  #to reconstruct the timing of the closed captions (i.e. how many seconds into
  #the file are they shown?)
  initial_timestamp = 0
  pes_packet = None
  pes = []
  for packet in next_ts_packet(infilename):
    #always process timestamp info, regardless of PID
    if packet.adapatation_field() and packet.adapatation_field().PCR():
      current_timestamp = packet.adapatation_field().PCR()
      initial_timestamp = initial_timestamp or current_timestamp
      delta = current_timestamp - initial_timestamp
      elapsed_time_s = float(delta)/90000.0
      #print('{i} {c} {d} {s}'.format(i=initial_timestamp, c=current_timestamp, d=delta, s=elapsed_time_s))

    #if this is the stream PID we're interestd in, reconstruct the ES
    if packet.pid() == pid:
      #print('packet of interest.')
      if packet.payload_start():
        #print('Payload start:' + str(packet.payload_start()))
        pes = copy.deepcopy(packet.payload())
        #print('initial length of packet payload is {l}'.format(l=len(pes)))
      else:
        #print('Packet continued.')
        #print('length of ts packet payload is {l}'.format(l=len(packet.payload())))
        pes.extend(packet.payload())
        #print('Current length of packet payload is {l}'.format(l=len(pes)))
      pes_packet = PESPacket(pes)
      

      #if our packet is fully formed (payload all present) we can parse its contents
      if pes_packet.length() == (pes_packet.header_size() + pes_packet.payload_size()):
        print('{s}'.format(s=elapsed_time_s))
        #print 'Pes packet length: {p} and header size {h} and payload length: {l}'.format(p=pes_packet.length(), h=pes_packet.header_size(), l=pes_packet.payload_size())
        #print u' '.join(u'{:#x}'.format(x) for x in pes_packet.payload())
        data_group = DataGroup(pes_packet.payload())

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
            cc = formatter(data_unit.payload().payload())
            if cc:
              #according to best practice, always deal internally with UNICODE, and encode to
              #your encoding of choice as late as possible. Here, i'm encoding as UTF-8 for
              #my command line.
              #DECODE EARLY, ENCODE LATE
              print(cc.encode('utf-8'))
    

if __name__ == "__main__":
  main()
