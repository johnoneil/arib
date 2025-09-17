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
import traceback
from arib.read import EOFError

from arib.mpeg.ts import TS
from arib.mpeg.ts import ES

from arib.closed_caption import next_data_unit
from arib.closed_caption import StatementBody
import arib.code_set as code_set
import arib.control_characters as control_characters
from arib.data_group import DataGroup

# print out some additional info for DRCS values
from arib.closed_caption import set_DRCS_debug
set_DRCS_debug(True)



DISPLAYED_CC_STATEMENTS = [
  code_set.Kanji,
  code_set.Alphanumeric,
  code_set.Hiragana,
  code_set.Katakana,
  code_set.DRCS0,
  code_set.DRCS1,
  code_set.DRCS2,
  code_set.DRCS3,
  code_set.DRCS4,
  code_set.DRCS5,
  code_set.DRCS6,
  code_set.DRCS7,
  code_set.DRCS8,
  code_set.DRCS9,
  code_set.DRCS10,
  code_set.DRCS11,
  code_set.DRCS12,
  code_set.DRCS13,
  code_set.DRCS14,
  code_set.DRCS15,
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
  control_characters.HLC,
]

# GLOBALS TO KEEP TRACK OF STATE
initial_timestamp = 0
elapsed_time_s = 0
pid = -1
VERBOSE = False
SILENT = False
DEBUG = False

def formatter(statements, timestamp):
  '''Turn a list of decoded closed caption statements
    into something we want (probably just plain text)
    Note we deal with unicode only here.
  '''
  # print('File elapsed time seconds: {s}'.format(s=timestamp))
  # line = ''.join([(s) for str(s) in statements if type(s) in DISPLAYED_CC_STATEMENTS])
  # return line
  allowed = tuple(DISPLAYED_CC_STATEMENTS)
  return ''.join(
    str(s) for s in statements
    if isinstance(s, allowed)
  )


def OnProgress(bytes_read, total_bytes, percent):
  """
  Callback method invoked on a change in file progress percent (not every packet)
  Meant as a lower frequency callback to update onscreen progress percent or something.
  :param bytes_read:
  :param total_bytes:
  :param percent:
  :return:
  """
  global VERBOSE
  global SILENT
  if not VERBOSE and not SILENT:
    #sys.stdout.write("progress: %.2f%%   \r" % (percent))
    #sys.stdout.flush()
    pass

def OnTSPacket(packet):
  """
  Callback invoked on the successful extraction of a single TS packet from a ts file
  :param packet: The entire packet (header and payload) as a string
  :return: None
  """
  global initial_timestamp
  global elapsed_time_s
  #pcr (program count record) can be used to calculate elapsed time in seconds
  # we've read through the .ts file
  pcr = TS.get_pcr(packet)
  if pcr > 0:
    current_timestamp = pcr
    initial_timestamp = initial_timestamp or current_timestamp
    delta = current_timestamp - initial_timestamp
    elapsed_time_s = float(delta) / 90000.0

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
  global pid
  global VERBOSE
  global SILENT
  global elapsed_time_s

  if pid >= 0 and current_pid != pid:
    return

  try:
    payload = ES.get_pes_payload(packet)
    f = list(payload)
    data_group = DataGroup(f)
    if not data_group.is_management_data():
      #We now have a Data Group that contains caption data.
      #We take out its payload, but this is further divided into 'Data Unit' structures
      caption = data_group.payload()
      #iterate through the Data Units in this payload via another generator.
      for data_unit in next_data_unit(caption):
        #we're only interested in those Data Units which are "statement body" to get CC data.
        if not isinstance(data_unit.payload(), StatementBody):
          continue

        # this code used to sed the PID we're scanning via first successful ARIB decode
        # but i've changed it below to draw present CC language info form ARIB
        # management data. Leaving this here for reference.
        #if pid < 0 and VERBOSE and not SILENT:
        #  pid = current_pid
        #  print("Found Closed Caption data in PID: " + str(pid))
        #  print("Will now only process this PID to improve performance.")

        #formatter function above. This dumps the basic text to stdout.
        cc = formatter(data_unit.payload().payload(), elapsed_time_s)
        if cc and VERBOSE:
          print(cc)
    else:
      # management data
      management_data = data_group.payload()
      numlang = management_data.num_languages()
      if pid < 0 and numlang > 0:
        for language in range(numlang):
          if not SILENT:
            print("Closed caption management data for language: "
              + management_data.language_code(language)
              + " available in PID: " + str(current_pid))
            print("Will now only process this PID to improve performance.")
        pid = current_pid

  except EOFError:
    pass
  except Exception as err:
    if VERBOSE and not SILENT and pid >= 0:
      print("Exception thrown while handling DataGroup in ES. This may be due to many factors"
         + "such as file corruption or the .ts file using as yet unsupported features.")
      traceback.print_exc(file=sys.stdout)


def main():
  global pid
  global VERBOSE

  parser = argparse.ArgumentParser(description='Draw CC Packets from MPG2 Transport Stream file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Transport Stream File)', type=str)
  parser.add_argument('-p', '--pid', help='Specify a PID of a PES known to contain closed caption info (tool will attempt to find the proper PID if not specified.).', type=int, default=-1)
  parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose output')
  args = parser.parse_args()

  infilename = args.infile
  pid = args.pid
  VERBOSE = args.verbose

  if not os.path.exists(infilename):
    print ('Input filename :' + infilename + " does not exist.")
    os.exit(-1)

  ts = TS(infilename)

  ts.Progress = OnProgress
  ts.OnTSPacket = OnTSPacket
  ts.OnESPacket = OnESPacket

  ts.Parse()


if __name__ == "__main__":
  main()
