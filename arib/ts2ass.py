#!/usr/bin/env python
# vim: set ts=2 expandtab:
'''
Module: ts2ass
Desc: Extract ARIB CCs from an MPEG transport stream and produce an .ass subtitle file off them.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Saturday, May 24th 2014

'''
import os
import sys
import argparse
import copy
from arib.data_group import next_data_group
from arib.closed_caption import next_data_unit
from arib.closed_caption import StatementBody
import arib.code_set as code_set
import arib.control_characters as control_characters
from arib.ts import next_ts_packet
from arib.ts import next_pes_packet
from arib.ts import TSPacket
from arib.ts import PESPacket
from arib.data_group import DataGroup

from arib.ass import ASSFormatter
from arib.ass import ASSFile

def main():
  parser = argparse.ArgumentParser(description='Remove ARIB formatted Closed Caption information from an MPEG TS file and format the results as a standard .ass subtitle file.')
  parser.add_argument('infile', help='Input filename (MPEG2 Transport Stream File)', type=str)
  parser.add_argument('-p', '--pid', help='Specify a PID of a PES known to contain closed caption info (tool will attempt to find the proper PID if not specified.).', type=int, default=-1)
  parser.add_argument('-v','--verbose', help='Verbose output.', action='store_true')
  parser.add_argument('-q','--quiet', help='Does not write to stdout.', action='store_true')
  parser.add_argument('-t','--tmax', help='Subtitle display time limit (seconds).', type=int, default=5)
  parser.add_argument('-o', '--timeoffset', help='Shift all time values in generated .ass file by indicated floating point offset in seconds.', type=float, default=0.0)
  args = parser.parse_args()

  pid = args.pid
  infilename = args.infile
  quiet = args.quiet
  verbose = args.verbose
  tmax = args.tmax
  time_offset = args.timeoffset

  if not os.path.exists(infilename):
    print 'Input filename :' + infilename + " does not exist."
    os.exit(-1)

  #open an Ass file and formatter
  ass_file = None #ASSFile(infilename+'.ass')
  ass = None #ASSFormatter(ass_file, tmax=tmax)

  #CC data is not, in itself timestamped, so we've got to use packet info
  #to reconstruct the timing of the closed captions (i.e. how many seconds into
  #the file are they shown?)
  initial_timestamp = 0
  pes_packet = None
  pes = []
  elapsed_time_s = 0
  # get filesize for progress meter
  total_filesize = os.path.getsize(infilename)
  read_size = 0
  percent_read = 0
  prev_percent_read = percent_read
  if not quiet and  not verbose:
    #show initial progress information
    sys.stdout.write("progress: %d%%   \r" % (percent_read) )
    sys.stdout.flush()

  for packet in next_ts_packet(infilename):
    read_size += TSPacket.PACKET_SIZE_BYTES
    percent_read =((read_size/float(total_filesize))* 100)
    new_percent_read = int(percent_read * 100)
    if not quiet and not verbose and new_percent_read != prev_percent_read:
        prev_percent_read = new_percent_read
        #print("totalsize:"+str(total_filesize)+" read_size "+str(read_size) + " percent: " + str(new_percent_read))
        sys.stdout.write("progress: %.2f%%   \r" % (percent_read) )
        sys.stdout.flush()

    #always process timestamp info, regardless of PID
    if packet.adapatation_field() and packet.adapatation_field().PCR():
      current_timestamp = packet.adapatation_field().PCR()
      initial_timestamp = initial_timestamp or current_timestamp
      delta = current_timestamp - initial_timestamp
      elapsed_time_s = float(delta)/90000.0 + time_offset

    #if this is the stream PID we're interestd in, reconstruct the ES
    if pid < 0 or ( pid == packet.pid() ):
      try:
          if packet.payload_start():
            pes = copy.deepcopy(packet.payload())
          else:
            pes.extend(packet.payload())
          pes_packet = PESPacket(pes)


          #if our packet is fully formed (payload all present) we can parse its contents
          if pes_packet.length() == (pes_packet.header_size() + pes_packet.payload_size()):

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

                # only write the file if we've actually found some Closed Captions
                if not ass_file:
                  ass_file = ASSFile(infilename+'.ass')
                if not ass:
                  ass = ASSFormatter(ass_file, tmax=tmax, video_filename=infilename)

                ass.format(data_unit.payload().payload(), elapsed_time_s)
                if pid < 0:
                    pid = packet.pid()
                    print("Found Closed Caption data in PID: "+str(pid))
                    print("Will now only process this PID to improve performance.")
                #print("properly formed packet with pid: "+ str(packet.pid()))
                #okay. Finally we've got a data unit with CC data. Feed its payload to the custom
                #formatter function above. This dumps the basic text to stdout.
                #cc = formatter(data_unit.payload().payload(), elapsed_time_s)
                #if cc:
                  #according to best practice, always deal internally with UNICODE, and encode to
                  #your encoding of choice as late as possible. Here, i'm encoding as UTF-8 for
                  #my command line.
                  #DECODE EARLY, ENCODE LATE
                  #print(cc.encode('utf-8'))
      except:
          if(pid >= 0):
            print("exception thrown while processing packet with PID: " + str(packet.pid()))
            print("This could indicate an application error, file corruption or this file uses features not yet supported by the application.");
          pass
  if pid < 0 or not ass:
    print("Did not find any Closed Caption data in the file " + infilename)

if __name__ == "__main__":
  main()
