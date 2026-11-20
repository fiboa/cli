# Contributing to fiboa CLI

Thanks for contributing! The [Development](README.md#development) section of the README explains the
setup. The guidelines below collect what reviews ask for most often.

## Responsibility and AI

- You are responsible for everything you contribute, no matter how it was made. Check all of it
  before you ask for a review: reviewing a contribution should take less work than making it.
- Comments, reviews and replies on GitHub that are addressed to people should be written by a human
  and concisely for a human.
- Saying in the PR that you used AI is appreciated. Commits don't need AI attribution, as the
  responsibility is entirely yours.

## Converters

- Follow [Implement a converter](README.md#implement-a-converter) and start from the
  [template](fiboa_cli/datasets/template.py).
- Prefer the declarative attributes of the template and the
  [base converter](https://github.com/vecorel/cli/blob/main/vecorel_cli/conversion/base.py) over
  overriding methods. `migrate` is the last resort.
- A conversion runs these steps in order:
  1. Download the `sources` and read them with `open_options`
  2. `file_migration` (per file), then reprojection to `crs`
  3. `migrate`
  4. `column_filters`
  5. `column_additions`
  6. `column_migrations`
  7. `post_migrate` (e.g. HCAT and crop names)
  8. Create the `id` (e.g. from `id_columns`) and drop rows that miss required values
  9. Rename the columns as listed in `columns`, fix the geometries, number repeated ids and drop all
     other columns

  Until step 9, the columns have the source's names.
- Don't re-implement what the base classes already do, and don't set attributes to their defaults.
- Generic behaviour belongs in vecorel-cli or a [shared mixin](fiboa_cli/datasets/commons), not in a
  single converter.
- Train/val/test splits go into a separate `<id>_ml` converter.

## IDs

- Converter IDs start with the country or region code where there is one (`de_bw`); `ec_` stands
  for EuroCrops. Don't rename published converters.
- Use stable source identifiers as feature `id`, so that they stay the same across editions.

## Code lists and data

- Code lists are CSV files in [fiboa.github.io](https://github.com/fiboa/fiboa.github.io/tree/main/code),
  not dicts in Python. Fix wrong codes or names there.
- Check what a source's codes mean before mapping them, and take crop names only from a table made
  for the same edition.
- Licenses are SPDX IDs, otherwise a link to the terms of use. Attributions must be complete.

## Tests

- Add a small fixture of real source data and register it in [test_convert.py](tests/test_convert.py)
  instead of writing custom tests for each converter.
- Keep tests proportionate, and make sure they cover what they claim to.

## Changelog and pull requests

- Every non-trivial change needs a `CHANGELOG.md` entry (CI checks it).
- Changelog entries are short and user-facing. Converter entries start with the upper-case ID
  (`DE-BW:`) and come sorted after the general ones.
- Keep PRs small and focused on one converter or topic, and say if a PR depends on another one.
- Keep code comments and PR descriptions short.
- Run `pixi run -e dev check` before pushing.
