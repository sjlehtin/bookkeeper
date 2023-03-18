import subprocess
import pytest
import pathlib
import shutil

TESTDATA_DIR = pathlib.Path(__file__).parent.parent / "testdata"


def test_bookkeeper_empty_directory(tmp_path):
    """
    This reproduces an issue in the release that caused a
    hard-to-understand exception to be thrown in case no data files were
    present in the current working directory.
    """
    shutil.copy(TESTDATA_DIR / "2012" / "ledger-defs.txt", tmp_path)

    with pytest.raises(subprocess.CalledProcessError) as e:
        subprocess.check_output(["bookkeeper", ".", ], stderr=subprocess.PIPE, cwd=tmp_path)

    assert b"No input files" in e.value.stderr