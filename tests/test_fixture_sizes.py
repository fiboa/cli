"""No source archive belongs in the test fixtures.

A convert test reads its input from `tests/data-files/convert/<id>/`, which is
also the cache folder it hands the converter — so a test that misses its fixture
downloads the real source into that folder, where `git add -A` will happily pick
it up. A 1.6 GB French RPG archive and a 1.9 GB Portuguese GeoPackage were both
caught by hand, one commit before being pushed.

The limit is generous: the largest fixture in the repository is 2 MB.
"""

import subprocess
from pathlib import Path

import pytest

FIXTURES = Path("tests/data-files")
LIMIT_MB = 5


def _git(*args) -> list[Path]:
    result = subprocess.run(
        ["git", *args, str(FIXTURES)], capture_output=True, text=True, check=True
    )
    return [Path(line) for line in result.stdout.split("\0") if line]


def oversized(paths, limit_mb: int = LIMIT_MB) -> list[tuple[Path, float]]:
    """The paths above the limit, largest first, with their size in MB."""
    found = [(p, p.stat().st_size / 1024 / 1024) for p in paths if p.is_file() and p.stat().st_size]
    return sorted([(p, mb) for p, mb in found if mb > limit_mb], key=lambda t: -t[1])


def _report(kind, offenders):
    lines = "\n".join(f"  {mb:8.1f} MB  {p}" for p, mb in offenders)
    return (
        f"{len(offenders)} {kind} fixture file(s) above {LIMIT_MB} MB:\n{lines}\n\n"
        "Fixtures are small samples (`ogr2ogr <out> -limit 100 <in>`). A file this "
        "large is almost certainly a source archive a failing convert test "
        "downloaded into the fixture folder; delete it and pin the test to the "
        "edition the fixture holds."
    )


def test_committed_fixtures_are_small():
    try:
        tracked = _git("ls-files", "-z")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("not a git checkout")
    offenders = oversized(tracked)
    assert not offenders, _report("committed", offenders)


def test_no_large_untracked_fixtures():
    """Untracked and not ignored is one `git add -A` away from being committed."""
    try:
        untracked = _git("ls-files", "-z", "--others", "--exclude-standard")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("not a git checkout")
    offenders = oversized(untracked)
    assert not offenders, _report("untracked", offenders)


def test_oversized_reports_the_biggest_first(tmp_path):
    small, big, bigger = tmp_path / "s", tmp_path / "b", tmp_path / "bb"
    small.write_bytes(b"x" * 1024)
    big.write_bytes(b"x" * 2 * 1024 * 1024)
    bigger.write_bytes(b"x" * 3 * 1024 * 1024)
    assert [p for p, _ in oversized([small, big, bigger], limit_mb=1)] == [bigger, big]
    assert oversized([small, big, bigger], limit_mb=5) == []
