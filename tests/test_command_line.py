import subprocess
import pytest
import pathlib
import shutil
import re


TESTDATA_DIR = pathlib.Path(__file__).parent.parent / "testdata"


def test_bookkeeper_empty_directory(tmp_path):
    """
    This reproduces an issue in the release that caused a
    hard-to-understand exception to be thrown in case no data files were
    present in the current working directory.
    """
    with pytest.raises(subprocess.CalledProcessError) as e:
        subprocess.check_output(["bookkeeper", ".", ], stderr=subprocess.PIPE, cwd=tmp_path)

    assert b"No input files" in e.value.stderr


def test_bookkeeper_no_transactions(no_transactions_directory):
    with pytest.raises(subprocess.CalledProcessError) as e:
        subprocess.check_output(["bookkeeper", ".", ], stderr=subprocess.PIPE, cwd=no_transactions_directory)

    assert b"No input files" in e.value.stderr



def test_bookkeeper_basic(simple_input_directory):
    output = subprocess.check_output(["bookkeeper", ".", ],
                                     stderr=subprocess.PIPE, cwd=simple_input_directory)

    assert re.search(rb"Output left in directory .*/output\.", output)


def test_bookkeeper_syntax_error_in_txdata(no_transactions_directory):

    with open(no_transactions_directory / "data-2012-01.txt", "w") as fp:
        fp.write("""\
guaranteed syntax error""")

    with pytest.raises(subprocess.CalledProcessError) as e:
        subprocess.check_output(["bookkeeper", ".", ], stderr=subprocess.PIPE, cwd=no_transactions_directory)

    assert b"data-2012-01.txt" in e.value.stderr
    assert b"Exception" not in e.value.stderr