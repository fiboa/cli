import json

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
