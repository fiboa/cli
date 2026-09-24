from urllib.parse import parse_qs, urlparse

import geopandas as gpd
import pytest
import spdx_license_list
from shapely.geometry import Point
from vecorel_cli.vecorel.schemas import VecorelSchema
from vecorel_cli.vecorel.util import load_file

from fiboa_cli.converters import Converters
from fiboa_cli.fiboa.version import get_fiboa_uri


def test_converters(capsys):
    from fiboa_cli import Registry  # noqa

    Converters().converters()
    out, err = capsys.readouterr()
    output = out + err

    assert "Short Title" in output
    assert "License" in output
    assert "at" in output
    assert "Austria" in output
    # assert "None" not in output


def test_changed_properties():
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        assert converter.license is None or isinstance(converter.license, str)
        assert converter.provider is None is None or isinstance(converter.provider, str)


def test_valid_license():
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        if converter.license and "<" not in converter.license:
            assert converter.license.upper() in spdx_license_list.LICENSES, (
                f"Converter {_id} has invalid license {converter.license}"
            )
        assert getattr(converter, "license") is None or isinstance(converter.license, str)
        assert getattr(converter, "provider") is None or isinstance(converter.provider, str)


def test_rest_query_params(monkeypatch, tmp_folder):
    """
    The paging filter must be combined with rest_params["where"] rather than replace it,
    and rest_format must drive both the "f" parameter and the cached page extension.
    """
    # lt_kzs is the converter that sets rest_format="json" and a rest_params["where"]
    converter = Converters().load("lt_kzs")
    converter.cache_folder = str(tmp_folder)

    class Response:
        def json(self):
            # maxRecordCount above the page length below, so paging stops after one page
            return {"layers": [{"id": 0}], "maxRecordCount": 1000}

    monkeypatch.setattr(
        "fiboa_cli.conversion.converter_rest.requests.get", lambda url, params: Response()
    )

    requested, read = [], []
    monkeypatch.setattr(
        "fiboa_cli.conversion.converter_rest.stream_file",
        lambda fs, uri, file: (requested.append(uri), file.write(b"{}")),
    )

    def fake_read_file(path, *args, **kwargs):
        read.append(path)
        return gpd.GeoDataFrame({"OBJECTID": [1]}, geometry=[Point(0, 0)], crs="EPSG:4326")

    monkeypatch.setattr(gpd, "read_file", fake_read_file)

    list(converter.get_data([converter.rest_base_url]))

    assert len(requested) == 1, "Expected exactly one page"
    query = parse_qs(urlparse(requested[0]).query)
    assert query["f"] == ["json"], "rest_format must drive the output format"
    assert query["outSR"] == ["4326"], "rest_params must survive into the query"
    assert query["where"] == ["OBJECTID>-1 AND (GKODAS IN ('bl1','bl1b'))"], (
        "The paging filter must be combined with rest_params['where'], not replace it"
    )
    assert read[0].endswith(".json"), (
        f"rest_format must drive the cached page extension, got {read[0]}"
    )


def test_overriden_base_properties():
    """
    You should not define a different schema for a property if it is defined in the base schema.
    """
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        schemas = converter.missing_schemas
        converter_properties = schemas and schemas.get("properties") or {}
        schema = VecorelSchema(load_file(get_fiboa_uri()))

        for property, s in schema["properties"].items():
            if property in converter_properties:
                assert s == converter_properties[property], (
                    "Converter {converter} overrides schema for base property {property}"
                )


def test_default_variant_reaches_a_converter_that_overrides_get_urls():
    """LV looks its files up by year and used to fail without --variant: the base
    get_urls() that chose the default was the method it replaced."""
    converter = Converters().load("lv")
    converter.select_variant(None)
    assert converter.variant == "2025"


def test_lv_requires_the_nine_regional_geopackages(monkeypatch):
    from fiboa_cli.datasets import lv

    # the portal's spellings: a trailing space in 2021, Lielrīga until 2023, Lielriga since
    regions = [
        "Austrumlatgale ",
        "Dienvidkurzeme",
        "Dienvidlatgale",
        "Lielrīga",
        "Viduslatvija",
        "Zemgale",
        "Ziemeļaustrumi",
        "Ziemeļkurzeme",
        "Ziemeļvidzeme",
    ]

    def package(title, names):
        resources = [
            {"name": name, "url": f"https://data.gov.lv/{i}/download/{i}.gpkg"}
            for i, name in enumerate(names)
        ]
        resources.append({"name": "Metadata", "url": "https://data.gov.lv/x/download/meta.pdf"})
        return {"title": title, "resources": resources}

    packages = [
        package("Lauksaimnieku deklarētās platības 2024.gadā", regions),
        package("Lauksaimnieku deklarētās platības 2023. gadā", regions[:-1]),
        # matched the search through its description, and carries the campaign pattern
        package("Cita datu kopa 2024. gadā", regions),
    ]

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"result": {"results": packages}}

    monkeypatch.setattr(lv.requests, "get", lambda *args, **kwargs: Response())
    converter = Converters().load("lv")

    converter.variant = "2024"
    assert sorted(converter.get_urls().values()) == [
        f"lv_2024_{region}.gpkg" for region in sorted(lv.REGIONS)
    ]

    converter.variant = "2023"
    with pytest.raises(RuntimeError, match="missing: ziemelvidzeme"):
        converter.get_urls()

    converter.variant = "2022"
    with pytest.raises(ValueError, match="found 0"):
        converter.get_urls()


def test_split_multipart_recomputes_the_metrics_of_the_parts():
    """explode() copies the source row's attributes onto every part, so the area and
    perimeter of a two-part feature would be published twice, for the whole feature."""
    from shapely.geometry import MultiPolygon, box

    from fiboa_cli.conversion.fiboa_converter import SPLIT_KEY, FiboaBaseConverter

    class Converter(FiboaBaseConverter):
        id = "split"
        columns = {
            "geometry": "geometry",
            "id": "id",
            "shape_area": "metrics:area",
            "shape_length": "metrics:perimeter",
        }
        area_is_in_ha = False

    two_parts = MultiPolygon([box(0, 0, 10, 10), box(20, 0, 50, 10)])  # 100 + 300 m²
    one_part = MultiPolygon([box(0, 20, 10, 40)])  # 200 m², a multi-part type but not split
    gdf = gpd.GeoDataFrame(
        {"id": ["a", "b"], "shape_area": [400.0, 200.0], "shape_length": [120.0, 60.0]},
        geometry=[two_parts, one_part],
        crs="EPSG:3059",
    )

    converter = Converter()
    gdf = converter.split_multipart(gdf)
    assert gdf["id"].tolist() == ["a", "a", "b"]

    gdf = converter.post_migrate(gdf)
    assert SPLIT_KEY not in gdf.columns
    assert gdf["shape_area"].tolist() == [100.0, 300.0, 200.0]
    assert gdf["shape_length"].tolist() == [40.0, 80.0, 60.0]


def _determination_converter(**attrs):
    from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

    columns = attrs.pop("columns", {"geometry": "geometry", "id": "id"})
    return type("Converter", (FiboaBaseConverter,), {"id": "det", "columns": columns, **attrs})()


def _determination(converter, variant):
    """The determination date the chosen variant adds as a constant column, if any."""
    converter.select_variant(variant)
    return converter.column_additions.get("determination:datetime")


def test_year_variants_default_to_the_variant_as_determination():
    """Without an explicit setting, year-like variants fill the determination date
    from the chosen variant (fiboa/cli#284)."""
    converter = _determination_converter(variants={str(y): str(y) for y in range(2024, 2019, -1)})
    assert _determination(converter, "2023") == "2023-01-01T00:00:00Z"


def test_the_default_variant_fills_the_determination():
    converter = _determination_converter(variants={"2023": "2023", "2024": "2024"})
    assert _determination(converter, None) == "2024-01-01T00:00:00Z"


def test_reselecting_a_variant_updates_the_determination():
    """The first date added must not count as provided by the converter."""
    converter = _determination_converter(variants={"2023": "2023", "2024": "2024"})
    _determination(converter, "2023")
    assert _determination(converter, "2024") == "2024-01-01T00:00:00Z"


def test_historical_year_variants_default_to_the_variant_as_determination():
    """The year range reaches back to 1900, so pre-2000 historical editions qualify too."""
    converter = _determination_converter(variants={"1995": "1995", "1996": "1996"})
    assert _determination(converter, "1995") == "1995-01-01T00:00:00Z"


def test_non_year_variants_do_not_default_to_determination():
    """Variants that are not years (e.g. region codes) carry no determination date."""
    converter = _determination_converter(variants={"north": "north", "south": "south"})
    assert _determination(converter, "north") is None


def test_no_variants_do_not_default_to_determination():
    converter = _determination_converter(variants={})
    assert _determination(converter, None) is None


def test_a_mapped_determination_is_not_overwritten_by_the_variant():
    """A converter that maps its own determination:datetime keeps it, even with year
    variants: the default only fills the gap, it never overrides."""
    converter = _determination_converter(
        variants={"2023": "2023"},
        columns={"geometry": "geometry", "id": "id", "campaign": "determination:datetime"},
    )
    assert _determination(converter, "2023") is None


def test_a_self_mapped_determination_is_not_overwritten_by_the_variant():
    """Mapping the key to itself means the converter fills the column in its own code
    (e.g. pl_block from the archive date), so the variant must not overwrite it."""
    converter = _determination_converter(
        variants={"2023": "2023"},
        columns={
            "geometry": "geometry",
            "id": "id",
            "determination:datetime": "determination:datetime",
        },
    )
    assert _determination(converter, "2023") is None


def test_a_constant_determination_is_not_overwritten_by_the_variant():
    converter = _determination_converter(
        variants={"2023": "2023"},
        column_additions={"determination:datetime": "2023-06-15T00:00:00Z"},
    )
    assert _determination(converter, "2023") == "2023-06-15T00:00:00Z"


def test_explicit_false_overrides_the_year_variant_default():
    converter = _determination_converter(
        variants={"2023": "2023"}, use_variant_as_determination=False
    )
    assert _determination(converter, "2023") is None


def test_explicit_true_fills_determination_for_non_year_variants():
    converter = _determination_converter(
        variants={"spring": "spring"}, use_variant_as_determination=True
    )
    assert _determination(converter, "spring") == "spring-01-01T00:00:00Z"


def test_explicit_true_without_a_variant_adds_no_determination():
    converter = _determination_converter(variants={}, use_variant_as_determination=True)
    assert _determination(converter, None) is None


def test_es_cl_defaults_to_the_latest_campaign():
    """ES-CL used to choose its year in get_urls(), after the determination is set."""
    from fiboa_cli.datasets.es_cl import ESCLConverter

    assert _determination(ESCLConverter(), None) == "2025-01-01T00:00:00Z"


def test_a_variant_without_crops_drops_the_crop_promises():
    """DK 2008 publishes fields without a crop, so it may not claim the schemas.

    The extensions are added in `__init__`, before a variant is chosen; only after
    `select_variant` can a converter know that this edition has nothing to map.
    """
    from fiboa_cli.datasets.commons.hcat import CROP_EXTENSION, HCAT_EXTENSION

    converter = Converters().load("dk")
    converter.select_variant("2008")

    assert CROP_EXTENSION not in converter.extensions
    assert HCAT_EXTENSION not in converter.extensions
    assert "hcat:code" not in converter.columns.values()
    assert "crop:code_list" not in converter.columns.values()


def test_a_normal_variant_keeps_them():
    from fiboa_cli.datasets.commons.hcat import CROP_EXTENSION, HCAT_EXTENSION

    converter = Converters().load("dk")
    converter.select_variant("2024")

    assert CROP_EXTENSION in converter.extensions
    assert HCAT_EXTENSION in converter.extensions
    assert "hcat:code" in converter.columns.values()


def test_reselecting_a_crop_variant_restores_the_crop_promises():
    from fiboa_cli.datasets.commons.hcat import CROP_EXTENSION, HCAT_EXTENSION

    converter = Converters().load("dk")
    converter.select_variant("2008")
    converter.select_variant("2024")

    assert CROP_EXTENSION in converter.extensions
    assert HCAT_EXTENSION in converter.extensions
    assert "hcat:code" in converter.columns.values()
    assert "crop:code_list" in converter.columns.values()


def test_a_missing_crop_column_still_fails_where_it_should():
    """The reason the opt-in is a list of variants and not a fallback: a typo or a
    column that disappears upstream must not quietly produce a file without HCAT."""
    converter = Converters().load("dk")
    converter.select_variant("2024")
    gdf = gpd.GeoDataFrame({"id": ["a"]}, geometry=[Point(0, 0)], crs="EPSG:4326")

    with pytest.raises(KeyError):
        converter.add_hcat(gdf)
