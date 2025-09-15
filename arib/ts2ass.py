#!/usr/bin/env python
# vim: set ts=2 expandtab:
"""
Module: ts2ass
Desc: Extract ARIB CCs from an MPEG transport stream and produce an .ass subtitle file off them.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Saturday, May 24th 2014
UPDATED: Saturday, Jan 12th 2017
"""

import os
import errno
import sys
import argparse
import traceback

from arib.read import EOFError

from arib.closed_caption import next_data_unit
from arib.closed_caption import StatementBody
from arib.data_group import DataGroup
from arib.arib_exceptions import FileOpenError

from arib.mpeg.ts import TS
from arib.mpeg.ts import ES

from arib.ass import ASSFormatter
from arib.ass import ASSFile

# GLOBALS TO KEEP TRACK OF STATE
initial_timestamp = None
elapsed_time_s = 0
pid = -1
VERBOSE = True
SILENT = False
DEBUG = True
ass = None
infilename = ""
outfilename = ""
tmax = 0


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
    sys.stdout.write("progress: %.2f%%   \r" % (percent))
    sys.stdout.flush()

def OnTSPacket(packet):
  """
  Callback invoked on the successful extraction of a single TS packet from a ts file
  :param packet: The entire packet (header and payload) as a string
  :return: None
  """
  global initial_timestamp
  global elapsed_time_s
  global time_offset

  #pcr (program count record) can be used to calculate elapsed time in seconds
  # we've read through the .ts file
  pcr = TS.get_pcr(packet)
  if pcr > 0:
    current_timestamp = pcr
    initial_timestamp = initial_timestamp or current_timestamp
    delta = current_timestamp - initial_timestamp
    elapsed_time_s = float(delta) / 90000.0 + time_offset

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
  global ass
  global infilename
  global outfilename
  global tmax
  global time_offset

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

        if not ass:
          v = not SILENT
          ass = ASSFormatter(tmax=tmax, video_filename=outfilename, verbose=v)

        ass.format(data_unit.payload().payload(), elapsed_time_s)

        # this code used to sed the PID we're scanning via first successful ARIB decode
        # but i've changed it below to draw present CC language info form ARIB
        # management data. Leaving this here for reference.
        #if pid < 0 and not SILENT:
        #  pid = current_pid
        #  print("Found Closed Caption data in PID: " + str(pid))
        #  print("Will now only process this PID to improve performance.")

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
  except FileOpenError as ex:
    # allow IOErrors to kill application
    raise ex
  except Exception as err:
    if not SILENT and pid >= 0:
      print("Exception thrown while handling DataGroup in ES. This may be due to many factors"
        + "such as file corruption or the .ts file using as yet unsupported features.")
      traceback.print_exc(file=sys.stdout)


def main():
  global pid
  global VERBOSE
  global SILENT
  global infilename
  global outfilename
  global tmax
  global time_offset

  parser = argparse.ArgumentParser(
    description='Remove ARIB formatted Closed Caption information from an MPEG TS file and format the results as a standard .ass subtitle file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Transport Stream File)', type=str)
  parser.add_argument('-o', '--outfile', help='Output filename (.ass subtitle file)', type=str, default=None)
  parser.add_argument('-p', '--pid',
                      help='Specify a PID of a PES known to contain closed caption info (tool will attempt to find the proper PID if not specified.).',
                      type=int, default=-1)
  parser.add_argument('-v', '--verbose', help='Verbose output.', action='store_true')
  parser.add_argument('-q', '--quiet', help='Does not write to stdout.', action='store_true')
  parser.add_argument('-t', '--tmax', help='Subtitle display time limit (seconds).', type=int, default=5)
  parser.add_argument('-m', '--timeoffset',
                      help='Shift all time values in generated .ass file by indicated floating point offset in seconds.',
                      type=float, default=0.0)
  args = parser.parse_args()

  pid = args.pid
  infilename = args.infile
  outfilename = infilename + ".ass"
  if args.outfile is not None:
    outfilename = args.outfile

  SILENT = args.quiet
  VERBOSE = args.verbose
  tmax = args.tmax
  time_offset = args.timeoffset

  if not os.path.exists(infilename) and not SILENT:
    print('Input filename :' + infilename + " does not exist.")
    sys.exit(-1)

  ts = TS(infilename)

  ts.Progress = OnProgress
  ts.OnTSPacket = OnTSPacket
  ts.OnESPacket = OnESPacket

  ts.Parse()

  if pid < 0 and not SILENT:
    print("*** Sorry. No ARIB subtitle content was found in file: " + infilename + " ***")
    sys.exit(-1)

  if ass and not ass.file_written() and not SILENT:
    print("*** Sorry. No nonempty ARIB closed caption content found in file " + infilename + " ***")
    sys.exit(-1)

  sys.exit(0)

if __name__ == "__main__":
  main()

