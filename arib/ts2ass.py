#!/usr/bin/env python3
"""
Module: ts2ass
Desc: Extract ARIB CCs from an MPEG transport stream and produce an .ass subtitle file..
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Saturday, May 24th 2014
UPDATED: Saturday, Jan 12th 2017
UPDATED: Saturday, Oct 4th, 2025
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from arib.arib_exceptions import FileOpenError
from arib.ass import ASSFormatter
from arib.closed_caption import StatementBody, next_data_unit
from arib.data_group import DataGroup
from arib.mpeg.ts import ES, TS
from arib.read import EOFError


@dataclass(frozen=True)
class Config:
    infile: Path
    outfile: Path
    pid: int
    verbose: bool
    quiet: bool
    tmax: int
    time_offset: float
    disable_drcs: bool
    disable_backgrounds: bool
    show_debug_grid: bool


class TS2ASS:
    def __init__(self, cfg: Config):
        self.cfg = cfg

        # state formerly in globals
        self.initial_timestamp: Optional[int] = None
        self.elapsed_time_s: float = 0.0
        self.pid: int = cfg.pid  # may be discovered later from mgmt data if -1
        self.ass: Optional[ASSFormatter] = None

    # ---- callbacks (former On* functions) ----

    def on_progress(self, bytes_read, total_bytes, percent):
        # preserve original behavior: show progress only when not verbose and not quiet
        if not self.cfg.verbose and not self.cfg.quiet:
            sys.stdout.write(f"progress: {percent:.2f}%   \r")
            sys.stdout.flush()

    def on_ts_packet(self, packet):
        # pcr can be used to calculate elapsed time in seconds through the .ts file
        pcr = TS.get_pcr(packet)
        if pcr > 0:
            current_timestamp = pcr
            self.initial_timestamp = self.initial_timestamp or current_timestamp
            delta = current_timestamp - self.initial_timestamp
            self.elapsed_time_s = float(delta) / 90000.0 + self.cfg.time_offset

    def on_es_packet(self, current_pid, packet, header_size):
        # honor fixed PID if provided
        if self.pid >= 0 and current_pid != self.pid:
            return

        try:
            payload = ES.get_pes_payload(packet)
            f = list(payload)
            data_group = DataGroup(f)
            if not data_group.is_management_data():
                # Data group contains caption data -> iterate data units
                caption = data_group.payload()
                for data_unit in next_data_unit(caption):
                    # Only interested in "statement body" units
                    if not isinstance(data_unit.payload(), StatementBody):
                        continue

                    if not self.ass:
                        v = not self.cfg.quiet
                        self.ass = ASSFormatter(
                            tmax=self.cfg.tmax,
                            video_filename=str(self.cfg.outfile),
                            verbose=v,
                            disable_drcs=self.cfg.disable_drcs,
                            disable_backgrounds=self.cfg.disable_backgrounds,
                            show_debug_grid=self.cfg.show_debug_grid,
                        )

                    self.ass.format(data_unit.payload().payload(), self.elapsed_time_s)

                # (Old commented PID detection code retained in spirit by mgmt data branch below)

            else:
                # management data
                management_data = data_group.payload()
                numlang = management_data.num_languages()
                if self.pid < 0 and numlang > 0:
                    for language in range(numlang):
                        if not self.cfg.quiet:
                            print(
                                "Closed caption management data for language: "
                                + management_data.language_code(language)
                                + " available in PID: "
                                + str(current_pid)
                            )
                            print("Will now only process this PID to improve performance.")
                    self.pid = current_pid

        except EOFError:
            pass
        except FileOpenError as ex:
            # allow IOErrors to kill application
            raise ex
        except Exception:
            # Preserve original behavior: print when we have (or found) a PID
            if not self.cfg.quiet and self.pid >= 0:
                print(
                    "Exception thrown while handling DataGroup in ES."
                    "This may be due to many factors "
                    + "such as file corruption or the .ts file using"
                    " as yet unsupported features."
                )
                traceback.print_exc(file=sys.stdout)

    # ---- driver ----

    def run(self) -> int:
        if not self.cfg.infile.exists() and not self.cfg.quiet:
            print(f"Input filename :{self.cfg.infile} does not exist.")
            return -1

        ts = TS(str(self.cfg.infile))
        ts.Progress = self.on_progress
        ts.OnTSPacket = self.on_ts_packet
        ts.OnESPacket = self.on_es_packet

        ts.Parse()

        if self.pid < 0 and not self.cfg.quiet:
            print(f"*** Sorry. No ARIB subtitle content was found in file: {self.cfg.infile} ***")
            return -1

        if self.ass and not self.ass.file_written() and not self.cfg.quiet:
            print(
                "*** Sorry. No nonempty ARIB closed caption content found in file "
                + str(self.cfg.infile)
                + " ***"
            )
            return -1

        return 0


def parse_args(argv=None) -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Remove ARIB formatted Closed Caption information from an MPEG TS file "
            "and format the results as a standard .ass subtitle file."
        )
    )
    parser.add_argument("infile", help="Input filename (MPEG2 Transport Stream File)", type=str)
    parser.add_argument(
        "-o", "--outfile", help="Output filename (.ass subtitle file)", type=str, default=None
    )
    parser.add_argument(
        "-p",
        "--pid",
        help=(
            "Specify a PID of a PES known to contain closed caption info "
            "(tool will attempt to find the proper PID if not specified.)."
        ),
        type=int,
        default=-1,
    )
    parser.add_argument("-v", "--verbose", help="Verbose output.", action="store_true")
    parser.add_argument("-q", "--quiet", help="Does not write to stdout.", action="store_true")
    parser.add_argument(
        "-t", "--tmax", help="Subtitle display time limit (seconds).", type=int, default=4
    )
    parser.add_argument(
        "-m",
        "--timeoffset",
        help=(
            "Shift all time values in generated .ass file"
            "by indicated floating point offset in seconds."
        ),
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--disable-drcs",
        help="Disable emitting .ass drawing code for runtime (dynamic) DRCS characters.",
        action="store_true",
    )
    parser.add_argument(
        "--disable-backgrounds",
        help="Disable shaded backgrounds behind on screen text.",
        action="store_true",
    )
    parser.add_argument(
        "--show-debug-grid",
        help="Generate a character position debug grid visible onscreen.",
        action="store_true",
    )
    args = parser.parse_args(argv)

    infile = Path(args.infile)
    outfile = Path(args.outfile) if args.outfile is not None else infile.with_suffix(".ass")

    return Config(
        infile=infile,
        outfile=outfile,
        pid=args.pid,
        verbose=bool(args.verbose),
        quiet=bool(args.quiet),
        tmax=int(args.tmax),
        time_offset=float(args.timeoffset),
        disable_drcs=bool(args.disable_drcs),
        disable_backgrounds=bool(args.disable_backgrounds),
        show_debug_grid=bool(args.show_debug_grid),
    )


def main(argv=None):
    cfg = parse_args(argv)
    app = TS2ASS(cfg)
    rc = app.run()
    sys.exit(rc)


if __name__ == "__main__":
    main()
