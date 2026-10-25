"""Tests for the JP converter's download path.

MAFF's download URLs only work signed, so the converter asks the API to sign the files
that are not cached yet. These tests answer the API with a fake service and record
what reaches the regular download.
"""

import os
import shutil

import pytest
from vecorel_cli.conversion.base import BaseConverter

from fiboa_cli.datasets import jp

FIXTURE = "tests/data-files/convert/jp/jp_fude_2026_13.zip"
NAMES = {"01": "北海道", "13": "東京都"}


class FakeAPI:
    """Signs every requested prefecture and records the requests."""

    def __init__(self):
        self.posts = []
        self.gets = []

    def get(self, url, headers=None, **kwargs):
        self.gets.append((url, headers))
        return FakeResponse([[{"pref_cd": c, "pref_name": n} for c, n in NAMES.items()]])

    def post(self, url, json=None, headers=None, **kwargs):
        self.posts.append((url, json, headers))
        found = [
            {"url": f"{jp.BASE}/{json['issue_year']}/{json['issue_year']}_{code}.zip?sig=x"}
            for code in json["pref_cd"]
        ]
        return FakeResponse({"found": found})


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


@pytest.fixture
def setup(monkeypatch, tmp_path):
    api = FakeAPI()
    monkeypatch.setattr(jp.requests, "get", api.get)
    monkeypatch.setattr(jp.requests, "post", api.post)

    downloads = []

    def download_files(self, uris, cache_folder=None, **kwargs):
        downloads.append((dict(uris), kwargs))
        paths = []
        for name in uris.values():
            path = tmp_path / "cache" / name
            if not path.exists():
                shutil.copy(FIXTURE, path)
            paths.append(str(path))
        return paths

    monkeypatch.setattr(BaseConverter, "download_files", download_files)
    (tmp_path / "cache").mkdir()

    converter = jp.JPConverter()
    converter.select_variant("2026")
    return converter, api, downloads, tmp_path / "cache"


def maff(pref):
    return f"{jp.BASE}/2026/2026_{pref}.zip"


def test_signs_the_missing_files_only(setup):
    converter, api, downloads, cache = setup
    shutil.copy(FIXTURE, cache / "jp_fude_2026_01.zip")
    uris = {maff("01"): "jp_fude_2026_01.zip", maff("13"): "jp_fude_2026_13.zip"}

    paths = converter.download_files(uris, str(cache))

    assert len(api.posts) == 1
    url, body, headers = api.posts[0]
    assert url.endswith("/download/lambda-download")
    assert body["issue_year"] == "2026"
    assert body["pref_cd"] == ["13"]
    assert body["pref_name"] == ["東京都"]
    assert headers == jp.HEADERS
    forwarded = {uri: name for batch, _ in downloads for uri, name in batch.items()}
    assert forwarded == {
        maff("01"): "jp_fude_2026_01.zip",
        f"{maff('13')}?sig=x": "jp_fude_2026_13.zip",
    }
    assert converter.request_headers == jp.HEADERS
    assert [os.path.basename(p) for p in paths] == [
        "jp_fude_2026_01.parquet",
        "jp_fude_2026_13.parquet",
    ]


def test_signs_everything_when_nothing_is_cached(setup):
    converter, api, downloads, cache = setup
    uris = {maff("01"): "jp_fude_2026_01.zip", maff("13"): "jp_fude_2026_13.zip"}

    converter.download_files(uris, str(cache))

    # each file is signed just before its download, as a signature lasts 30 minutes
    assert [body["pref_cd"] for _, body, _ in api.posts] == [["01"], ["13"]]
    assert [body["pref_name"] for _, body, _ in api.posts] == [["北海道"], ["東京都"]]
    assert [list(batch) for batch, _ in downloads] == [
        [f"{maff('01')}?sig=x"],
        [f"{maff('13')}?sig=x"],
    ]


def test_a_complete_cache_needs_no_api(setup):
    converter, api, downloads, cache = setup
    shutil.copy(FIXTURE, cache / "jp_fude_2026_13.zip")

    converter.download_files({maff("13"): "jp_fude_2026_13.zip"}, str(cache))

    assert api.posts == [] and api.gets == []
    assert downloads[0][0] == {maff("13"): "jp_fude_2026_13.zip"}


def test_other_urls_are_not_signed(setup):
    converter, api, downloads, cache = setup
    mirror = "https://mirror.example/tokyo.zip"

    converter.download_files({mirror: "jp_fude_2026_13.zip"}, str(cache))

    assert api.posts == [] and api.gets == []
    assert downloads[0][0] == {mirror: "jp_fude_2026_13.zip"}
