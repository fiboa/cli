from glob import glob

import pyarrow.parquet as pq
from click.testing import CliRunner

from fiboa_cli import merge, validate

"""
Create input files with:

$ for i in at be_wal nl; do fiboa convert $i -o tests/data-files/merge/$i.parquet -c tests/data-files/convert/$i; done
"""


def test_merge(tmp_file):
    # merge files in directory
    files = glob("tests/data-files/merge/*.parquet")
    runner = CliRunner()
    args = files + ["-o", tmp_file.name]
    result = runner.invoke(merge, args)
    assert result.exit_code == 0, result.output

    # Merged parquet file should be valid
    result = runner.invoke(validate, [tmp_file.name, "--data"])
    assert result.exit_code == 0, result.output

    data = pq.read_table(tmp_file.name)
    assert data.num_rows == 112

    fields = {f.name for f in pq.read_table(tmp_file.name).schema}
    assert {"area", "determination_datetime", "id", "geometry"}.issubset(fields)
