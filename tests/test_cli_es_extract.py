import sys
import pytest
import arib.es_extract as cli

# List of input .es files to run the CLI against
ES_FILES = [
    "tests/ace_of_diamond_subs_pid276.es",
    "tests/chibi_maruko_chan.es",
    "tests/one_piss.es",
    "tests/toriko_subs.es",
    "tests/aibou.es",
    "tests/detective_conan_846.es",
    "tests/pokemon-2023.es",
    "tests/aijin.es",
    "tests/dragonball-61.es",
    "tests/samurai_flamenco_13.es",
    "tests/chibi_maruko_chan_11May2014.es",
    "tests/gaki_defence_force.es",
    "tests/sangatsu-no-lion-4.es",
]


@pytest.mark.parametrize("input_file", ES_FILES)
def test_cli_runs_on_sample_files(monkeypatch, input_file):
    # Pretend we ran: arib-es-extract input_file
    monkeypatch.setattr(sys, "argv", ["arib-es-extract", input_file])

    # Run the main function. If it raises, the test fails.
    cli.main()
