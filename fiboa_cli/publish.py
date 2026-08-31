import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from vecorel_cli.basecommand import BaseCommand, runnable
from vecorel_cli.cli.options import VECOREL_TARGET

from .convert import ConvertData
from .converters import Converters
from .create_stac import CreateStacCollection
from .registry import Registry
from .validate import ValidateData

FILE_EXTENSION = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
WEB_MAP_LINKS_EXTENSION = "https://stac-extensions.github.io/web-map-links/v1.3.0/schema.json"
PMTILES_MEDIA_TYPE = "application/vnd.pmtiles"
TIPPECANOE_DEFAULT_OPTS = "-zg --drop-densest-as-needed --extend-zooms-if-still-dropping"

is_windows = os.name == "nt"


def multihash_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    sha2-256 multihash of a file, hex encoded: 0x12 (sha2-256), 0x20 (32 bytes), digest.
    This is the encoding the STAC file extension expects for ``file:checksum``.
    """
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            digest.update(chunk)
    return "1220" + digest.hexdigest()


class Publish(BaseCommand):
    cmd_name = "publish"
    cmd_help = (
        f"Convert a {Registry.project} dataset and prepare it for publication: "
        "GeoParquet, PMTiles and a STAC Collection with relative links."
    )

    @staticmethod
    def get_cli_args():
        return {
            **ConvertData.get_cli_args(),
            "target": VECOREL_TARGET(folder=True),
            "pmtiles": click.option(
                "--pmtiles/--no-pmtiles",
                is_flag=True,
                help="Generate PMTiles with ogr2ogr and tippecanoe.",
                default=True,
                show_default=True,
            ),
            "tippecanoe_opts": click.option(
                "--tippecanoe-opts",
                type=click.STRING,
                help="Additional options passed to tippecanoe.",
                default=TIPPECANOE_DEFAULT_OPTS,
                show_default=True,
            ),
        }

    @staticmethod
    def get_cli_callback(cmd):
        def callback(dataset, *args, **kwargs):
            return Publish(dataset).run(*args, **kwargs)

        return callback

    def __init__(self, dataset: str):
        super().__init__()
        self.cmd_title = f"Publish {dataset}"
        self.dataset = dataset

        try:
            self.converter = Converters().load(self.dataset)
        except (ImportError, NameError, OSError, RuntimeError, SyntaxError) as e:
            raise Exception(f"Converter for '{self.dataset}' not available or faulty: {e}") from e

    def check_command(self, cmd, name=None):
        if shutil.which(cmd) is None:
            self.error(f"Missing command {cmd}. Please install {name or cmd}")
            sys.exit(1)

    @runnable
    def publish(
        self,
        target,
        pmtiles=True,
        tippecanoe_opts=TIPPECANOE_DEFAULT_OPTS,
        **kwargs,
    ):
        """
        Creates the following files in the target folder:

        - <dataset>[-<variant>].parquet: the converted and validated fiboa GeoParquet file
        - <dataset>[-<variant>].pmtiles: vector tiles for visualization (ogr2ogr + tippecanoe)
        - collection.json: a STAC Collection with relative links to the files above

        Existing files are reused, delete them to regenerate.
        PMTiles generation needs GDAL 3.8 or later (for ogr2ogr) and tippecanoe:
        - https://gdal.org/
        - https://github.com/felt/tippecanoe
        """
        target = Path(target)
        target.mkdir(parents=True, exist_ok=True)

        file_name = self.dataset
        if not kwargs.get("variant") and self.converter.variants:
            kwargs["variant"] = next(iter(self.converter.variants))
        if kwargs.get("variant"):
            file_name += f"-{kwargs['variant']}"
        parquet_file = target / f"{file_name}.parquet"
        pmtiles_file = target / f"{file_name}.pmtiles"
        stac_file = target / "collection.json"

        # Create parquet file
        if not parquet_file.exists():
            self.info(f"Converting {self.dataset} to {parquet_file}")
            ConvertData(self.dataset).run(parquet_file, **kwargs)
            self.success(f"Converted {self.dataset} to {parquet_file}")
        else:
            self.success(f"Using existing file {parquet_file}")

        self.ensure_spatial_order(parquet_file)

        # Validate parquet file, we only want to publish valid files
        self.info(f"Validating {parquet_file}")
        ValidateData().validate(parquet_file, num=-1)
        self.log("\n  => VALID\n", "success")

        # Create PMTiles
        if pmtiles:
            self.generate_pmtiles(parquet_file, pmtiles_file, tippecanoe_opts)
        has_pmtiles = pmtiles_file.exists()

        # Create STAC collection.json
        self.create_stac_collection(parquet_file, pmtiles_file if has_pmtiles else None, stac_file)
        self.success(f"Created {stac_file}")
        return stac_file

    def create_stac_collection(self, parquet_file: Path, pmtiles_file, stac_file: Path):
        is_current = (
            stac_file.exists()
            and stac_file.stat().st_mtime >= parquet_file.stat().st_mtime
            and (pmtiles_file is None or stac_file.stat().st_mtime >= pmtiles_file.stat().st_mtime)
        )
        if is_current:
            self.info(f"Reusing existing {stac_file}")
            return

        self.info(f"Creating STAC collection for {parquet_file}")
        data = CreateStacCollection().create_from_file(
            parquet_file, data_url=f"./{parquet_file.name}"
        )
        if data["id"] != self.dataset:
            raise Exception(
                f"Wrong collection id: {data['id']} != {self.dataset}, for {parquet_file}"
            )

        extensions = data.setdefault("stac_extensions", [])
        if FILE_EXTENSION not in extensions:
            extensions.append(FILE_EXTENSION)

        asset = data["assets"]["data"]
        asset["title"] = f"{data.get('title') or self.dataset} (GeoParquet)"
        asset.update(self.file_metadata(parquet_file))

        if pmtiles_file is not None:
            if WEB_MAP_LINKS_EXTENSION not in extensions:
                extensions.append(WEB_MAP_LINKS_EXTENSION)
            data["links"] = [link for link in data.get("links", []) if link.get("rel") != "pmtiles"]
            data["links"].append(
                {
                    "rel": "pmtiles",
                    "href": f"./{pmtiles_file.name}",
                    "type": PMTILES_MEDIA_TYPE,
                    "title": "Web map tiles",
                    "pmtiles:layers": [self.dataset],
                }
            )
            data["assets"]["visual"] = {
                "href": f"./{pmtiles_file.name}",
                "type": PMTILES_MEDIA_TYPE,
                "title": f"{data.get('title') or self.dataset} (PMTiles)",
                "roles": ["visual"],
                **self.file_metadata(pmtiles_file),
            }

        with stac_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def file_metadata(path: Path) -> dict:
        return {
            "file:size": path.stat().st_size,
            "file:checksum": multihash_sha256(path),
        }

    # ~50k rows per group: inside gpio's spatial-query sweet spot, and with a
    # Hilbert order every small group is finer bbox-skipping granularity
    ROW_GROUP_SIZE = 50_000

    def ensure_spatial_order(self, parquet_file: Path):
        """Hilbert-sort the file in place unless it already is sorted.

        Every write path ends up spatially ordered regardless of converter
        (plain pandas, per-file merge, DuckDB), and re-running publish over an
        existing parquet doubles as the repair tool for published data."""
        import json as _json

        import pyarrow.parquet as _pq
        from vecorel_cli.vecorel.hilbert import crs_total_bounds

        from .conversion.per_file import _ensure_hilbert_sorted

        with _pq.ParquetFile(parquet_file) as pf:
            meta = pf.schema_arrow.metadata or {}
        if b"geo" not in meta:
            self.warning(f"{parquet_file} has no geo metadata; skipping spatial ordering")
            return
        geo = _json.loads(meta[b"geo"])
        primary = geo["primary_column"]
        crs = geo["columns"][primary].get("crs") or "EPSG:4326"
        if _ensure_hilbert_sorted(
            str(parquet_file),
            primary,
            crs_total_bounds(crs),
            "zstd",
            None,
            row_group_size=self.ROW_GROUP_SIZE,
        ):
            self.success(f"Re-sorted {parquet_file} into Hilbert order")

    def generate_pmtiles(self, parquet_file: Path, pmtiles_file: Path, tippecanoe_opts: str):
        if is_windows:
            self.warning(
                "PMTiles generation through tippecanoe is not supported on Windows, skipping."
            )
            return
        if pmtiles_file.exists():
            self.success(f"Using existing file {pmtiles_file}")
            return

        self.check_command("tippecanoe")
        self.check_command("ogr2ogr", name="GDAL")
        self.info("Running ogr2ogr | tippecanoe")
        ogr = subprocess.Popen(
            [
                "ogr2ogr",
                "-t_srs",
                "EPSG:4326",
                "-f",
                "GeoJSONSeq",
                "/vsistdout/",
                str(parquet_file),
            ],
            stdout=subprocess.PIPE,
        )
        # tippecanoe ignores $TMPDIR and spills into /tmp, which is often a small partition
        tmpdir = os.environ.get("TMPDIR")
        tmp_opts = ["-t", tmpdir] if tmpdir else []
        tippecanoe = subprocess.run(
            [
                "tippecanoe",
                *tmp_opts,
                *tippecanoe_opts.split(),
                "--projection=EPSG:4326",
                "-o",
                str(pmtiles_file),
                "-l",
                self.dataset,
            ],
            stdin=ogr.stdout,
        )
        ogr.stdout.close()
        ogr.wait()
        if ogr.returncode != 0 or tippecanoe.returncode != 0:
            pmtiles_file.unlink(missing_ok=True)
            raise Exception("PMTiles generation failed, see output above.")
        self.success(f"Created {pmtiles_file}")
