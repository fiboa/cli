# Agent guidelines

Rules for anyone (human or AI) changing fiboa CLI, collected from recurring review comments.

## Converters

- Start from `fiboa_cli/datasets/template.py` and use its declarative hooks first, e.g. 
  `sources`/`variants`, `columns`, `column_additions`, `column_filters`, `column_migrations`,
  `missing_schemas`, `extensions`, `area_is_in_ha`, `id_columns`, `open_options`, `crs`, `side_files`.
- Override methods only for what no hook covers. `file_migration` is for per-file logic (file name, row
  order); `migrate` is the fallback, not the main working mode. Overriding `read_data`, `get_data` or
  `download_files` should be the exception and often can go upstream into vecorel-cli.
- Don't re-implement what the base classes already do, e.g. dropping Z values, reprojecting
  (`crs`), unit conversion (`area_is_in_ha`), numbering repeated ids, choosing the default variant.
- If a converter needs a workaround for missing generic behaviour, fix it in vecorel-cli (or a shared
  mixin in `datasets/commons`) instead of in the converter.
- Reuse the mixins, e.g. `AddHCATMixin`, `CodeListMixin`,
  `EuroCropsConverterMixin`, `AdminConverterMixin`, `WFSConverterMixin`, `EsriRESTConverterMixin`.
- Train/val/test splits go into a separate `<id>_ml` converter with `MlSplitsMixin`.
- Don't set attributes to their default values, and don't declare what the schemas already define.

## IDs

- The converter ID is the module name and starts with the ISO 3166 code (`de_bw`, `in_10k`).
- Avoid renaming the ID of a published converter: it is the collection id of published data.
- Prefer stable source identifiers for `id`, so that ids stay the same across editions. Use
  `id_columns` to compose them instead of building strings by hand.

## Code lists and data

- Code lists are CSV files published on fiboa.org (fiboa/fiboa.github.io, `code/`), not dicts in
  Python. Fix wrong names or codes in those tables, not in converter code.
- Take crop names from a table only if it was made for the edition of the data
  (`crop_names_from_table`); codes get reused with other meanings across editions.
- Verify what a source's codes mean before mapping them (e.g. to HCAT); don't guess.
- Licenses are SPDX IDs (e.g. `CC-BY-4.0`, `CC0-1.0`). Without a license, link to the terms of use.
  Attributions must be complete.

## Tests

- Add a small fixture of real source data and register the converter in `tests/test_convert.py`
  (`tests`, `extra_convert_parameters`, `expected_columns`) instead of writing repetitive custom tests.
- Keep tests proportionate
- Tests and fixtures must actually exercise the code paths they are meant to cover.

## Changelog and PRs

- Every non-trivial change needs a `CHANGELOG.md` entry (CI checks it).
- Changelog entries are short and user-facing, without internals, in Added / Changed / Fixed / etc. Converter entries
  start with the upper-case id (`DE-BW:`), are sorted by it and come after general entries.
- Keep PRs small and focused (one converter or one topic) and target `main`. Say if a PR depends on
  another one.
- Write `#123` only for issues and PRs of this repository, `owner/repo#123` for others, and no `#` in
  front of other numbers.
- Keep code comments, PR descriptions and review replies short. Answer questions in a sentence or two.
- Run `pixi run check` (lint, format, tests) before pushing.
