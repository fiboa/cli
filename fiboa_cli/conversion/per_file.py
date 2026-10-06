import os
from tempfile import TemporaryDirectory

from vecorel_cli.conversion.duckdb import DuckDBBaseConverter


class PerFileConverterMixin:
    """Converts each source file on its own and merges the parts, for sources too large to read at once."""

    def convert(self, output_file, cache=None, input_files=None, variant=None, **kwargs) -> str:
        self.select_variant(variant)
        urls = input_files or self.get_urls()
        if not urls or len(urls) == 1:
            return super().convert(
                output_file, cache=cache, input_files=input_files, variant=variant, **kwargs
            )

        directory = os.path.dirname(output_file) or "."
        os.makedirs(directory, exist_ok=True)
        with TemporaryDirectory(dir=directory) as parts_folder:
            parts = []
            for index, (uri, target) in enumerate(urls.items()):
                self.info(f"Converting source {index + 1}/{len(urls)}: {uri}")
                part = os.path.join(parts_folder, f"part_{index}.parquet")
                super().convert(
                    part, cache=cache, input_files={uri: target}, variant=variant, **kwargs
                )
                parts.append(part)

            self.info(f"Merging {len(parts)} parts into {output_file}")
            merge_options = ("compression", "compression_level", "geoparquet_version")
            return DuckDBBaseConverter().merge_parquet(
                parts, output_file, **{k: kwargs[k] for k in merge_options if k in kwargs}
            )
