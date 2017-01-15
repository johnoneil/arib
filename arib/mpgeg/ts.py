#!/usr/bin/env python
'''
Module: ts
Desc: Minimalist MPEG ts packet parsing
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


class ES:
  """ very minimalistic Elementary Stream handling
  """
  STREAM_ID_INDEX = 3

  @staticmethod
  def pes_packet_check_formedness(payload):
    """ Check formedness of pes packet and indicate we have the entire payload
    """
    b1 = ord(payload[0])
    b2 = ord(payload[1])
    b3 = ord(payload[2])

    b4 = ord(payload[3])
    if b1 != 0 or b2 != 0 or b3 != 1:
      return False
    return True

  @staticmethod
  def get_pes_stream_id(payload):
    return ord(payload[ES.STREAM_ID_INDEX])

  @staticmethod
  def get_pes_packet_length(payload):
    if len(payload)<6:
      return 0
    # we add 6 for start code, stream id and pes packet length itself
    return struct.unpack('>H', payload[4:6])[0] + 6

  @staticmethod
  def get_pes_flags(payload):
    return struct.unpack('>H', payload[6:8])[0]

  @staticmethod
  def get_pes_header_length(payload):
    # 6 is initial prefix, streamid and then pes packet length
    # 3 is for header flags and header size value
    # value at byte 8 gives the remaining bytes in the header including stuffing
    if len(payload) < 9:
      return 0
    return 6 + 3 + ord(payload[8])

  @staticmethod
  def get_pes_payload_length(payload):
    return get_pes_packet_length(payload) - get_pes_header_length(payload)

  @staticmethod
  def get_pes_payload(payload):
    payload_start = get_pes_header_length(payload)
    return payload[payload_start:]

  @staticmethod
  def pes_packet_complete(payload):
    pes_packet_len = ES.get_pes_packet_length(payload)
    payload_len = len(payload)
    return pes_packet_len == payload_len


class TS(object):
  """ very minimalistic Transport stream handling
  """
  PACKET_SIZE = 188
  
  # Sync byte
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

  @staticmethod
  def next_packet(filename, memorymap=True):
    """ Generator to remove a series of TS packets from a TS file
    """
    with open(filename, 'rb') as f:
      
      #memory map the file if necessary (prob requires 64 bit systems)
      _file = f
      if memorymap:
        _file = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
      
      while True:
        packet = _file.read(TS.PACKET_SIZE)
        if packet:
          # first byte SHOULD be the sync byte
          # but if it isn't find one.
          if packet[0] != TS.SYNC_BYTE:
            start_byte = 0
            print packet[0]
            for i in range(start_byte, TS.PACKET_SIZE):
              if packet[i] == TS.SYNC_BYTE:
                start_byte = i
                break
            # didn't find a new start? FAIL
            if start_byte == 0:
              raise Exception("failure to find sync byte in ts packet size.")
              continue
            remainder = _file.read(TS.PACKET_SIZE - start_byte)
            packet = packet[start_byte:] + remainder
          yield packet
        else:
          break

  @staticmethod
  def check_packet_formedness(packet):
    """Check some features of this packet and see if it's well formed or not
    """
    if len(packet) != TS.PACKET_SIZE:
      raise Exception("Provided input packet string not of correct size")

    if packet[0] != TS.SYNC_BYTE:
      raise Exception("Provided input packet does not begin with correct sync byte.")

 
  @staticmethod
  def get_transport_error_indicator(packet):
    return (ord(packet[TS.TEI_INDEX]) & TS.TEI_MASK) != 0

  @staticmethod
  def get_payload_start(packet):
    return (ord(packet[TS.PUSI_INDEX]) & TS.PUSI_MASK) != 0

  @staticmethod
  def get_pid(packet):
    """Given a stringified MPEG TS packet, extract the PID value
    and return it as a simple integer value.
    Do this as quickly as possible for performance
    """
    return ((ord(packet[TS.PID_START_INDEX]) & 0x1f)<<8) | ord(packet[TS.PID_START_INDEX+1])

  @staticmethod
  def get_tsc(packet):
    """get value of Transport Scrambling Control indicato
    """
    return (ord(packet[TS.TSC_INDEX]) & TS.TSC_MASK) >> 6

  @staticmethod
  def get_adaptation_field_control(packet):
    """ get the adaptation field control value for this packet
    """
    return (ord(packet[TS.ADAPTATION_FIELD_CONTROL_INDEX]) & TS.ADAPTATION_FIELD_CONTROL_MASK) >> 4

  @staticmethod
  def get_continuity_counter(packet):
    """ Get the continuity counter value for this packet
    """
    return ord(packet[TS.CONTINUITY_COUNTER_INDEX]) & TS.CONTINUITY_COUNTER_MASK

  @staticmethod
  def get_adaptation_field_length(packet):
    """ Get the length of the adaptation field for this packet.
    Can return 0 if none is present.
    """
    if TS.get_adaptation_field_control(packet) == TS.NO_ADAPTATION_FIELD:
      return 0

    #we add one byte here for the adaptation field length data itself
    return ord(packet[TS.ADAPTATION_FIELD_LENGTH_INDEX]) + 1

  @staticmethod
  def adaptation_field_present(packet):
    return TS.get_adaptation_field_control(packet) != TS.NO_ADAPTATION_FIELD

  @staticmethod
  def get_pcr(packet):
    """ Get the Program Clock Reference for this packet if present.
    Can return 0 if data not present.
    """
    if not TS.adaptation_field_present(packet):
      return 0
    if not ord(packet[TS.ADAPTATION_FIELD_DATA_INDEX]) & TS.PCR_FLAG_MASK:
      return 0
    b1 = struct.unpack('>L', packet[TS.PCR_START_INDEX:TS.PCR_START_INDEX+4])[0]
    b2 = struct.unpack('>H', packet[TS.PCR_START_INDEX+4:TS.PCR_START_INDEX+6])[0]
    base = b1 << 1 | b2 >> 15 # 33 bit base
    extension = b2 & 0x1ff # 9 bit exstension
    return base * 300 + extension

  @staticmethod
  def pcr_delta_time_ms(pcr_t1, pcr_t2, offset = 0):
    """Return a floating point time in milliseconds representing the
    Difference in time between two PCR timestamps
    """
    return float(pcr_t2-pcr_t1)/90000.0 + offset


  @staticmethod
  def get_payload_length(packet):
    """Payload length from an 188 byte ts packet
    """
    adaptation_field_len = TS.get_adaptation_field_length(packet)
    return 188 - 4 - adaptation_field_len

  @staticmethod
  def get_payload(packet):
    """ return a byte array deep copy of 188 byte ts packet payload
    """
    #payload_len = get_payload_length(packet)
    adaptation_field_len = TS.get_adaptation_field_length(packet)
    header_size = 4 + adaptation_field_len
    return packet[header_size:]


  def __init__(self, filename):
    self._filename = filename
    self._total_filesize = os.path.getsize(filename)
    self._read_size = 0
    self.Progress = None
    self.OnTSPacket = None
    self.OnESPacket = None
    self.OnTSPacketError = None
    self.OnESPacketError = None
    self._elementary_streams = {}

  def Parse(self):
    """ Go through the .ts file, and invoke a callback on each TS packet and ES packet
    Also invoke progress callbacks and packet error callbacks as appropriate
    """
    prev_percent_read = 0
    for packet in TS.next_packet(self._filename):
      #check_packet_formedness(packet)
      pei = TS.get_transport_error_indicator(packet)
      pusi = TS.get_payload_start(packet)
      pid = TS.get_pid(packet)
      tsc = TS.get_tsc(packet)

      # per .ts packet handler
      if self.OnTSPacket:
        self.OnTSPacket(packet)

      # Update a progress callback
      self._read_size += TS.PACKET_SIZE
      percent_read = ((self._read_size  / float(self._total_filesize)) * 100)
      new_percent_read = int(percent_read * 100)
      if new_percent_read != prev_percent_read and self.Progress:
        self.Progress(self._read_size, self._total_filesize, percent_read)
        prev_percent_read = new_percent_read

      adaptation_field_control = TS.get_adaptation_field_control(packet)
      continuity_counter = TS.get_continuity_counter(packet)

      # put together PES from payloads
      payload = TS.get_payload(packet)
      if pusi == True:
        if not ES.pes_packet_check_formedness(payload):
          if pid in self._elementary_streams:
            elementary_streams[pid] = None
          continue
        pes_id = ES.get_pes_stream_id(payload)
        self._elementary_streams[pid] = payload
      else:
        if pid in self._elementary_streams:
          # TODO: check packet sequence counter
          self._elementary_streams[pid] += payload
        else:
          # TODO: throw. this situaiton means out of order packets
          pass
      if pid in self._elementary_streams and ES.pes_packet_complete(self._elementary_streams[pid]):
        # TODO: handle packet contents here (callback)
        es = self._elementary_streams[pid]
        if self.OnESPacket:
          header_size = ES.get_pes_header_length(es)
          self.OnESPacket(pid, es, header_size)


# GLOBALS TO KEEP TRACK OF STATE
initial_timestamp = 0
elapsed_time_s = 0


def OnProgress(bytes_read, total_bytes, percent):
  """
  Callback method invoked on a change in file progress percent (not every packet)
  Meant as a lower frequency callback to update onscreen progress percent or something.
  :param bytes_read:
  :param total_bytes:
  :param percent:
  :return:
  """
  sys.stdout.write("progress: %.2f%%   \r" % (percent))
  sys.stdout.flush()

def OnTSPacket(packet):
  """
  Callback invoked on the successful extraction of a single TS packet from a ts file
  :param packet: The entire packet (header and payload) as a string
  :return: None
  """
  global initial_timestamp
  #pcr (program count record) can be used to calculate elapsed time in seconds
  # we've read through the .ts file
  pcr = TS.get_pcr(packet)
  current_timestamp = pcr
  initial_timestamp = initial_timestamp or current_timestamp
  delta = current_timestamp - initial_timestamp
  elapsed_time_s = float(delta)/90000.0

def OnESPacket(current_pid, packet, header_size):
  """
  Callback invoked on the successful extraction of an Elementary Stream packet from the
  Transport Stream file packets.
  :param current_pid: The TS Program ID for the TS packets this info originated from
  :param packet: The ENTIRE ES packet, header and payload-- which may have been assembled
    from multiple TS packet payloads.
  :param header_size: Size of the header in bytes (characters in the string). Provided to more
    easily separate the packet into header and payload.
  :return: None
  """
  pass

def main():

  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Transport Stream file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Transport Stream File)', type=str)
  args = parser.parse_args()

  infilename = args.infile

  if not os.path.exists(infilename):
    print 'Input filename :' + infilename + " does not exist."
    os.exit(-1)

  ts = TS(infilename)

  ts.Progress = OnProgress
  ts.OnTSPacket = OnTSPacket
  ts.OnESPacket = OnESPacket

  ts.Parse()


if __name__ == "__main__":
  main()
