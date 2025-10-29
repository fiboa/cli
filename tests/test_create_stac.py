from pathlib import Path

from vecorel_cli.vecorel.util import load_file

from fiboa_cli.create_stac import CreateFiboaStacCollection
from fiboa_cli.registry import Registry


def test_create_stac_collection(tmp_folder: Path):
    source = Path("tests/data-files/fiboa-example.json")
    expected_file = "tests/data-files/stac-collection.json"
    out_file = tmp_folder / "collection.json"

    gj = CreateFiboaStacCollection()
    gj.create_cli(source, out_file)

    assert out_file.exists()

    created_file = load_file(out_file)
    expected = load_file(expected_file)
    assert isinstance(created_file, dict), "Created file is not a valid JSON dict"

    def pop_path(*args, value=None):
        c, e = created_file, expected
        for index, arg in enumerate(args):
            assert arg in c, f"{arg} not in created stac {c}"
            assert arg in e, f"{arg} not in expected {e}"
            method = dict.pop if index == len(args) - 1 else dict.get
            c, e = method(c, arg), method(e, arg)
        if value is not None:
            assert c == value, f"{c} != {value}"

    # Cater for environment differences in paths
    pop_path("assets", "data", "href")

    # Cater for floating point differences
    pop_path("extent", "spatial", "bbox")

    # Cater for differences in version numbers
    pop_path("assets", "data", "processing:software", "fiboa-cli", value=Registry.get_version())

    created_file["vecorel_extensions"]["de_nrw"].sort()
    expected["vecorel_extensions"]["de_nrw"].sort()

    assert created_file == expected
