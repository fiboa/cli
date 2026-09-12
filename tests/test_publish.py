import json
from types import SimpleNamespace

from pytest import mark, raises

import fiboa_cli.publish as publish_module
from fiboa_cli.publish import Publish


class PublishTest(Publish):
    def generate_pmtiles(self, parquet_file, pmtiles_file, tippecanoe_opts):
        # tippecanoe is not available everywhere, fake the tiles
        pmtiles_file.write_bytes(b"PMTiles")


def test_publish(tmp_folder):
    converter = "be_vlg"
    path = f"tests/data-files/convert/{converter}"
    PublishTest(converter).run(variant="2023", target=tmp_folder, cache=path)

    files = [f.name for f in tmp_folder.iterdir() if f.is_file()]
    for f in ("collection.json", "be_vlg-2023.parquet", "be_vlg-2023.pmtiles"):
        assert f in files, f"Missing file {f}"

    with open(tmp_folder / "collection.json") as f:
        stac = json.load(f)

    assert stac["id"] == converter
    assert "https://stac-extensions.github.io/file/v2.1.0/schema.json" in stac["stac_extensions"]
    assert (
        "https://stac-extensions.github.io/web-map-links/v1.3.0/schema.json"
        in stac["stac_extensions"]
    )

    data = stac["assets"]["data"]
    assert data["href"] == "./be_vlg-2023.parquet"
    assert data["file:size"] == (tmp_folder / "be_vlg-2023.parquet").stat().st_size
    assert data["file:checksum"].startswith("1220") and len(data["file:checksum"]) == 68

    visual = stac["assets"]["visual"]
    assert visual["href"] == "./be_vlg-2023.pmtiles"
    assert visual["roles"] == ["visual"]
    assert visual["file:size"] == 7

    pmtiles = next(link for link in stac["links"] if link["rel"] == "pmtiles")
    assert pmtiles["href"] == "./be_vlg-2023.pmtiles"
    assert pmtiles["pmtiles:layers"] == [converter]


class FakeOgr:
    returncode = 0

    def __init__(self, argv, stdout=None):
        self.argv = argv
        self.stdout = stdout

    def wait(self):
        return self.returncode


def _fake_tippecanoe(monkeypatch, tippecanoe_returncode=0, writes=None):
    """Run generate_pmtiles without ogr2ogr or tippecanoe, recording their argv."""
    calls = {}

    class FakeStdout:
        def close(self):
            calls["closed"] = True

    def popen(argv, stdout=None):
        calls["ogr"] = argv
        return FakeOgr(argv, FakeStdout())

    def run(argv, stdin=None):
        calls["tippecanoe"] = argv
        if writes is not None:
            writes.write_bytes(b"half a tile pyramid")
        return SimpleNamespace(returncode=tippecanoe_returncode)

    monkeypatch.setattr(publish_module.subprocess, "Popen", popen)
    monkeypatch.setattr(publish_module.subprocess, "run", run)
    monkeypatch.setattr(Publish, "check_command", lambda self, *args, **kwargs: None)
    return calls


@mark.skipif(publish_module.is_windows, reason="tippecanoe is not run on Windows")
def test_generate_pmtiles_hands_tippecanoe_the_temp_dir(tmp_folder, monkeypatch):
    """tippecanoe ignores $TMPDIR and spills into /tmp, which on the conversion
    server is a 3.8 GB partition — every early PMTiles failure came from that."""
    calls = _fake_tippecanoe(monkeypatch)
    monkeypatch.setenv("TMPDIR", str(tmp_folder))

    pmtiles = tmp_folder / "out.pmtiles"
    Publish("be_vlg").generate_pmtiles(tmp_folder / "in.parquet", pmtiles, "-z12 --drop-densest")

    assert calls["ogr"][:2] == ["ogr2ogr", "-t_srs"]
    assert calls["tippecanoe"][:3] == ["tippecanoe", "-t", str(tmp_folder)]
    assert "-z12" in calls["tippecanoe"] and "--drop-densest" in calls["tippecanoe"]
    assert calls["tippecanoe"][-1] == "be_vlg"  # the layer is named after the dataset
    assert calls["closed"]


@mark.skipif(publish_module.is_windows, reason="tippecanoe is not run on Windows")
def test_generate_pmtiles_removes_a_failed_file(tmp_folder, monkeypatch):
    """A half-written .pmtiles would be published as if it held the tiles."""
    pmtiles = tmp_folder / "half.pmtiles"
    _fake_tippecanoe(monkeypatch, tippecanoe_returncode=1, writes=pmtiles)
    monkeypatch.delenv("TMPDIR", raising=False)

    with raises(Exception, match="PMTiles generation failed"):
        Publish("be_vlg").generate_pmtiles(tmp_folder / "in.parquet", pmtiles, "-z12")

    assert not pmtiles.exists()


def test_generate_pmtiles_keeps_an_existing_file(tmp_folder, monkeypatch):
    """Rebuilding a year must not spend half an hour retiling what is there."""

    def fail(*args, **kwargs):
        raise AssertionError("tippecanoe should not run")

    monkeypatch.setattr(publish_module.subprocess, "Popen", fail)
    pmtiles = tmp_folder / "kept.pmtiles"
    pmtiles.write_bytes(b"PMTiles")

    Publish("be_vlg").generate_pmtiles(tmp_folder / "in.parquet", pmtiles, "-z12")

    assert pmtiles.read_bytes() == b"PMTiles"
