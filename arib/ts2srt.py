#!/usr/bin/env python3
"""
Module: ts2srt
Desc: Extract ARIB CCs from an MPEG transport stream and produce an .srt subtitle file off them.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Saturday, Oct 4th 2025
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from arib.arib_exceptions import FileOpenError
from arib.closed_caption import StatementBody, next_data_unit
from arib.data_group import DataGroup
from arib.mpeg.ts import ES, TS
from arib.read import EOFError
from arib.srt import SRTFormatter


@dataclass(frozen=True)
class Config:
    infile: Path
    outfile: Path
    pid: int
    verbose: bool
    quiet: bool
    tmax: int
    time_offset: float
    enable_small_text: bool
    output_to_stdout: bool


class TS2srt:
    def __init__(self, cfg: Config):
        self.cfg = cfg

        # state formerly in globals
        self.initial_timestamp: Optional[int] = None
        self.elapsed_time_s: float = 0.0
        self.pid: int = cfg.pid  # may be discovered later from mgmt data if -1
        self.srt: Optional[SRTFormatter] = None

    # ---- callbacks (former On* functions) ----

    def on_progress(self, bytes_read, total_bytes, percent):
        # preserve original behavior: show progress only when not verbose and not quiet
        if not self.cfg.verbose and not self.cfg.quiet and not self.cfg.output_to_stdout:
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

                    if not self.srt:
                        v = not self.cfg.quiet
                        self.srt = SRTFormatter(
                            tmax=self.cfg.tmax,
                            video_filename=str(self.cfg.outfile),
                            verbose=v,
                            enable_small_text=self.cfg.enable_small_text,
                            output_to_stdout=self.cfg.output_to_stdout,
                        )

                    self.srt.format(data_unit.payload().payload(), self.elapsed_time_s)

                # (Old commented PID detection code retained in spirit by mgmt data branch below)

            else:
                # management data
                management_data = data_group.payload()
                numlang = management_data.num_languages()
                if self.pid < 0 and numlang > 0:
                    for language in range(numlang):
                        if not self.cfg.quiet and not self.cfg.output_to_stdout:
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
                    "such as file corruption or the .ts file using"
                    " as yet unsupported features."
                )
                traceback.print_exc(file=sys.stdout)

    # ---- driver ----

    def run(self) -> int:
        not_quiet = not self.cfg.quiet

        if not self.cfg.infile.exists():
            if not_quiet:
                print(f"Input filename :{self.cfg.infile} does not exist.")
            return -1

        ts = TS(str(self.cfg.infile))
        ts.Progress = self.on_progress
        ts.OnTSPacket = self.on_ts_packet
        ts.OnESPacket = self.on_es_packet

        try:
            try:
                ts.Parse()
            except KeyboardInterrupt:
                if not_quiet:
                    print("Interrupted by user.")
                return 130  # conventional SIGINT exit
        finally:
            # Ensure buffered subtitle data is written to disk even if parsing
            # encounters errors partway through the file
            if self.srt:
                self.srt.finalize()

        # If we never found a usable PID, report "no ARIB subtitle content".
        if self.pid < 0:
            if not_quiet:
                print(
                    "*** Sorry. No ARIB subtitle content"
                    f" was found in file: {self.cfg.infile} ***"
                )
            return -1

        # Success conditions:
        # - stdout mode (no file to check)
        # - non-empty outfile on disk
        # - formatter believes it wrote (fallback)
        if self.cfg.output_to_stdout:
            return 0

        try:
            if self.cfg.outfile.exists() and self.cfg.outfile.stat().st_size > 0:
                return 0
        except OSError:
            pass  # fall back to formatter flag

        if self.srt and getattr(self.srt, "file_written", None) and self.srt.file_written():
            return 0

        if not_quiet:
            print(
                f"*** Sorry. No nonempty ARIB closed caption content found in file "
                f"{self.cfg.infile} ***"
            )
        return -1


def parse_args(argv=None) -> Config:
    parser = argparse.ArgumentParser(
        description=(
            "Remove ARIB formatted Closed Caption information from an MPEG TS file "
            "and format the results as a standard .srt subtitle file."
        )
    )
    parser.add_argument("infile", help="Input filename (MPEG2 Transport Stream File)", type=str)
    parser.add_argument(
        "-o", "--outfile", help="Output filename (.srt subtitle file)", type=str, default=None
    )
    parser.add_argument("--stdout", help="Output .srt content to stdout.", action="store_true")
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
            "Shift all time values in generated .srt file"
            "by indicated floating point offset in seconds."
        ),
        type=float,
        default=0.0,
    )
    parser.add_argument(
        "--enable-small-text",
        help=(
            "Enable the extraction of small (furigana or ruby) text" "and emit it to the .srt file."
        ),
        action="store_true",
    )
    args = parser.parse_args(argv)

    infile = Path(args.infile)
    outfile = Path(args.outfile) if args.outfile is not None else infile.with_suffix(".srt")

    return Config(
        infile=infile,
        outfile=outfile,
        pid=args.pid,
        verbose=bool(args.verbose),
        quiet=bool(args.quiet),
        tmax=int(args.tmax),
        time_offset=float(args.timeoffset),
        enable_small_text=bool(args.enable_small_text),
        output_to_stdout=bool(args.stdout),
    )


def main(argv=None):
    cfg = parse_args(argv)
    app = TS2srt(cfg)
    rc = app.run()
    sys.exit(rc)


if __name__ == "__main__":
    main()
