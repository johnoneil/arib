#!/usr/bin/python
# vim: set ts=2 expandtab:
'''
Module: ts.py
Desc: Take apart an MPEG Transport Stream
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, May 16th 2014 

Take apart an MPEG Transport Stream.
This is only a basic implementation because i'm currently
only interested in packet timestamp info.
  
''' 

import read
import os
import sys
import argparse
from arib_exceptions import DecodingError
from struct import error as struct_error
from copy import copy

'''
http://en.wikipedia.org/wiki/MPEG_transport_stream

Adaptation Field Length   8   0xff  Number of bytes in the adaptation field immediately following this byte
Discontinuity indicator   1   0x80  Set to 1 if current TS packet is in a discontinuity state with respect to either the continuity counter or the program clock reference
Random Access indicator   1   0x40  Set to 1 if the PES packet in this TS packet starts a video/audio sequence
Elementary stream priority indicator  1   0x20  1 = higher priority
PCR flag  1   0x10  Set to 1 if adaptation field contains a PCR field
OPCR flag   1   0x08  Set to 1 if adaptation field contains an OPCR field
Splicing point flag   1   0x04  Set to 1 if adaptation field contains a splice countdown field
Transport private data flag   1   0x02  Set to 1 if adaptation field contains private data bytes
Adaptation field extension flag   1   0x01  Set to 1 if adaptation field contains an extension
Below fields are optional   variable    Depends on flags
PCR   33+6+9    Program clock reference, stored in 6 octets in big-endian as 33 bits base, 6 bits padding, 9 bits extension.
OPCR  33+6+9    Original Program clock reference. Helps when one TS is copied into another
Splice countdown  8   0xff  Indicates how many TS packets from this one a splicing point occurs (may be negative)
stuffing bytes  variable
'''

class AdaptationField(object):
  '''Optional Transport Stream packet adaptation fieild
  '''
  def __init__(self, f):
    '''Initialize object off of file descriptor
    '''
    self._discontinuity_indicator = False
    self._random_access_indicator = False
    self._es_priority_indicator = False
    self._pcr_flag = False
    self._ocr_flag = False
    self._splicing_point_flag = False
    self._transport_private_data_flag = False
    self._adaptation_field_extension_flag = False
    self._payload = []
    self._pcr = 0
    self._ocr = 0

    self._adaptation_field_length = read.ucb(f)
    #Adaptation field length CAN be zero if only one byte stuffing is needed
    #So we only draw out other info when it's nonzero.
    if self._adaptation_field_length == 0:
      return
    bytes_read = 0
    flags = read.ucb(f)
    #print('flags {f:02X}'.format(f=flags))
    bytes_read += 1
    self._discontinuity_indicator = bool(flags & 0x80)
    self._random_access_indicator = bool(flags & 0x40)
    self._es_priority_indicator = bool(flags & 0x20)
    self._pcr_flag = bool(flags & 0x10)
    self._ocr_flag = bool(flags & 0x08)
    self._splicing_point_flag = bool(flags & 0x04)
    self._transport_private_data_flag = bool(flags & 0x20)
    self._adaptation_field_extension_flag = bool(flags & 0x01)

    if self._pcr_flag:
      self._pcr = read.uib(f)
      additional_bytes= read.usb(f)
      self._pcr = (self._pcr<<1)|((additional_bytes>>15))
      bytes_read += 6
    if self._ocr_flag:
      self._ocr = read.uib(f)
      additional_bytes = read.usb(f)
      bytes_read += 6

    #print ('af length {l} and bytes read {b}'.format(l=self._adaptation_field_length, b=bytes_read))
    self._payload = [read.ucb(f) for x in range(self._adaptation_field_length-bytes_read)]

  def PCR(self):
    return self._pcr

  def OCR(self):
    return self._ocr

  def __len__(self):
    return self._adaptation_field_length + 1


class TSPacket(object):
  '''Represents standard 188 byte MPEG TS packet
  '''
  SYNC_BYTE = 0x47
  PACKET_SIZE_BYTES =  188
  
  def __init__(self, f):
    '''Copy packet data from file f to structure
    '''
    sync_byte = read.ucb(f)
    if sync_byte != TSPacket.SYNC_BYTE:
      raise DecodingError("Incorrect sync byte found at start of TS packet.")
    pid_bytes = read.usb(f)
    self._pid = 0x0fff & pid_bytes
    self._payload_start_indicator = bool(0xf000 & pid_bytes)

    #(2 bit scrambling control =00, 1 bit adaptation exists=true, 1 bit payload exists=true, 4 bit continuity counter =0xc)
    flags_byte = read.ucb(f)
    self._scrambling_control = 0xc0 & flags_byte
    self._adaptation_field_exists = bool(0x20 & flags_byte)
    self._payload_exists = bool(0x10 & flags_byte)
    self._continuity_counter = 0x0f & flags_byte

    if self._adaptation_field_exists:
      self._adaptation_field = AdaptationField(f)
      self._payload = [read.ucb(f) for x in range(188-4-len(self._adaptation_field))]
    else:
      self._payload = [read.ucb(f) for x in range(188-4)]

  def payload(self):
    return self._payload

  def adapatation_field(self):
    if not self._adaptation_field_exists:
      return None
    return self._adaptation_field


def next_ts_packet(filepath):
  '''Given the path to a .TS file, generate
  a series of TS packets structures.
  '''
  f = open(filepath, "rb")
  packet = TSPacket(f)
  try:
    while packet:
      yield packet
      packet = TSPacket(f)
  except struct_error:
    pass
  finally:
    f.close()
  


def main():
  '''Simple main that demonstrates going through a .ts file
  and draing out timestap information from all packets
  '''
  parser = argparse.ArgumentParser(description='Test parsing of MPEG Transport Stream file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Elmentary Stream)', type=str)
  #parser.add_argument('-p', '--pid', help='Pid of stream .', type=str, default='')
  args = parser.parse_args()

  infilename = args.infile
  if not os.path.exists(infilename):
    print 'Please provide input Transport Stream file.'
    os.exit(-1)

  initial_timestamp = 0
  
  for packet in next_ts_packet(infilename):
    #print('PID: {pid}'.format(pid=str(packet._pid)))
    if packet.adapatation_field() and packet.adapatation_field().PCR():
      current_timestamp = packet.adapatation_field().PCR()
      initial_timestamp = initial_timestamp or current_timestamp
      delta = current_timestamp - initial_timestamp
      elapsed_time_s = float(delta)/90000.0
      print('{i} {c} {d} {s}'.format(i=initial_timestamp, c=current_timestamp, d=delta, s=elapsed_time_s))
        
if __name__ == "__main__":
  main()

