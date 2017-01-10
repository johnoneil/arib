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
import struct

# memorymap file on 64 bit systems
import platform
import mmap

PACKET_SIZE = 188
# sync byte
SYNC_BYTE_INDEX = 0
SYNC_BYTE = 'G'
# Transport Error Indicator (TEI)
TEI_INDEX = 1
TEI_MASK = 0x80
# Payload Unit Start Indicator (PUSI)
PUSI_INDEX = 1
PUSI_MASK = 0x40
#Packt ID (PID)
PID_START_INDEX = 1
PID_LENGTH_BYTES = 2
PID_MASK = 0x1fff
# Transport Scrambling Control (TSC)
TSC_INDEX = 3
TSC_MASK = 0xc0
# Adaptation field control
ADAPTATION_FIELD_CONTROL_INDEX = 3
ADAPTATION_FIELD_CONTROL_MASK = 0x30
NO_ADAPTATION_FIELD = 0b01
ADAPTATION_FIELD_ONLY = 0b10
ADAPTATION_FIELD_AND_PAYLOAD = 0b11
ADAPTATION_FIELD_RESERVED = 0b00
# Continuity counter
CONTINUITY_COUNTER_INDEX = 3
CONTINUITY_COUNTER_MASK = 0x0f

# Adaptation field data (if present)
ADAPTATION_FIELD_LENGTH_INDEX = 4
ADAPTATION_FIELD_DATA_INDEX = 5

# Program Clock Reference (PCR)
# Present flag tagged in ADAPTATION_FIELD_DATA_INDEX byte
PCR_FLAG_MASK = 0x10
PCR_START_INDEX = 6 
PCR_SIZE_BYTES = 6

def check_packet_formedness(packet):
  """Check some features of this packet and see if it's well formed or not
  """
  if len(packet) != PACKET_SIZE:
    raise Exception("Provided input packet string not of correct size")

  if packet[0] != SYNC_BYTE:
    raise Exception("Provided input packet does not begin with correct sync byte.")

#generator
def next_packet(filename, memorymap=True):
  with open(filename, 'rb') as f:
    
    #memory map the file if necessary (prob requires 64 bit systems)
    _file = f
    if memorymap:
      _file = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
    
    while True:
      packet = _file.read(PACKET_SIZE)
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
          remainder = _file.read(PACKET_SIZE - start_byte)
          packet = packet[start_byte:] + remainder
        yield packet
      else:
        break

def get_transport_error_indicator(packet):
  return (ord(packet[TEI_INDEX]) & TEI_MASK) == 1

def get_payload_start(packet):
  return (ord(packet[PUSI_INDEX]) & PUSI_MASK) == 1

def get_pid(packet):
  """Given a stringified MPEG TS packet, extract the PID value
  and return it as a simple integer value.
  Do this as quickly as possible for performance
  """
  return ((ord(packet[PID_START_INDEX]) & 0x1f)<<8) | ord(packet[PID_START_INDEX+1])

def get_tsc(packet):
  """get value of Transport Scrambling Control indicato
  """
  return (ord(packet[TSC_INDEX]) & TSC_MASK) >> 6

def get_adaptation_field_control(packet):
  """ get the adaptation field control value for this packet
  """
  return (ord(packet[ADAPTATION_FIELD_CONTROL_INDEX]) & ADAPTATION_FIELD_CONTROL_MASK) >> 4

def get_continuity_counter(packet):
  """ Get the continuity counter value for this packet
  """
  return ord(packet[CONTINUITY_COUNTER_INDEX]) & CONTINUITY_COUNTER_MASK

def get_adaptation_field_length(packet):
  """ Get the length of the adaptation field for this packet.
  Can return 0 if none is present.
  """
  if get_adaptation_field_control(packet) == NO_ADAPTATION_FIELD:
    return 0

  return ord(packet[ADAPTATION_FIELD_LENGTH_INDEX])

def adaptation_field_present(packet):
  return get_adaptation_field_control(packet) != NO_ADAPTATION_FIELD

def get_pcr(packet):
  """ Get the Program Clock Reference for this packet if present.
  Can return 0 if data not present.
  """
  if not adaptation_field_present(packet):
    return 0
  if not ord(packet[ADAPTATION_FIELD_DATA_INDEX]) & PCR_FLAG_MASK:
    return 0
  b1 = struct.unpack('>L', packet[PCR_START_INDEX:PCR_START_INDEX+4])[0]
  b2 = struct.unpack('>H', packet[PCR_START_INDEX+4:PCR_START_INDEX+6])[0]
  base = b1 << 1 | b2 >> 15 # 33 bit base
  extension = b2 & 0x1ff # 9 bit exstension
  return base * 300 + extension

def pcr_delta_time_ms(pcr_t1, pcr_t2, offset = 0):
  """Return a floating point time in milliseconds representing the
  Difference in time between two PCR timestamps
  """
  return float(pcr_t2-pcr_t1)/90000.0 + offset


def get_payload_length(packet):
  """Payload length from an 188 byte ts packet
  """
  adaptation_field_len = get_adaptation_field_length(packet)
  return 188 - 4 - adaptation_field_len

def get_payload(packet):
  """ return a byte array deep copy of 188 byte ts packet payload
  """
  payload_len = get_payload_length(packet)
  return packet[:-payload_len]

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

  # Show on-screen progress info.
  sys.stdout.write("progress: %d%%   \r" % (percent_read) )
  sys.stdout.flush()
 
  initial_timestamp = None

  #turn off memory mapping files on 32 bit systems
  memory_mapping = True
  if platform.architecture()[0] != '64bit':
    memor_mapping = False;

  current_payload = None

  for packet in next_packet(infilename, memory_mapping):

    # Show on-screen progress info.
    read_size += PACKET_SIZE
    percent_read =((read_size/float(total_filesize))* 100)
    new_percent_read = int(percent_read * 100)
    if new_percent_read != prev_percent_read:
      prev_percent_read = new_percent_read
      sys.stdout.write("progress: %.2f%%   \r" % (percent_read) )
      sys.stdout.flush()
    
    # extract data from packet to do a "worst case" access test
    check_packet_formedness(packet)
    pei = get_transport_error_indicator(packet)
    pusi = get_payload_start(packet)
    pid = get_pid(packet)
    tsc = get_tsc(packet)
    adaptation_field_control = get_adaptation_field_control(packet)
    continuity_counter = get_continuity_counter(packet)
    pcr = get_pcr(packet)
    if pcr > 0:
      if not initial_timestamp:
        initial_timestamp = pcr
      #print "elapsed time: " + str(pcr_delta_time_ms(initial_timestamp, pcr))
    if not current_payload or get_payload_start(packet):
      current_payload = get_payload(packet)
    else:
      current_payload += get_payload(packet)

if __name__ == "__main__":
  main()
