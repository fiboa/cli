"""The IDEAragon discovery path, which the conversion fixture bypasses."""

from unittest.mock import patch

from pytest import raises

from fiboa_cli.datasets.es_ar import ARConverter

# One product per shape the service returns: a municipality of the province asked
# for, a municipality of a neighbour the intersection also matches, and a
# province-level archive. Only the first is wanted.
PRODUCTS = {
    "44": [
        {"name": "44216", "esquema": "Municipio", "fecha": "2025-03-01"},
        {"name": "22007", "esquema": "Municipio", "fecha": "2025-03-01"},
        {"name": "44", "esquema": "Provincia", "fecha": "2026-02-01"},
    ],
    "22": [{"name": "22007", "esquema": "Municipio", "fecha": "2026-03-01"}],
    "50": [],
}


def test_get_urls_keeps_the_provinces_own_municipalities():
    with patch.object(ARConverter, "list_products", staticmethod(lambda p: PRODUCTS[p])):
        urls = ARConverter().get_urls()

    assert sorted(urls.values()) == ["es_ar_22007.shp.zip", "es_ar_44216.shp.zip"]
    assert all("/CartoTema/sigpac/" in url for url in urls)
    assert "/CartoTema/sigpac/44216.shp.zip" in "".join(urls)


def test_get_urls_takes_the_newest_campaign_of_the_files_it_keeps():
    with patch.object(ARConverter, "list_products", staticmethod(lambda p: PRODUCTS[p])):
        converter = ARConverter()
        converter.get_urls()

    assert converter.edition_year == "2026"


def test_get_urls_refuses_an_empty_product_list():
    with patch.object(ARConverter, "list_products", staticmethod(lambda p: [])):
        with raises(ValueError, match="No SIGPAC municipality files"):
            ARConverter().get_urls()
