The gpkg is built up out of multiple layers, only the field boundary layers should be loaded:
`Culturas_<district>` up to 2023, `T<NUTS 3 code>` from 2025 on.

The test files are created by taking the first 100 features from these different layers.
Downloaded data is assumed in $DOWNLOADED_SOURCE. Run

```
ogr2ogr Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg Continente -limit 100
ogr2ogr -update Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg Culturas_Aveiro -limit 100
ogr2ogr -update Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg OcupacoesSolo_Aveiro -limit 100

ogr2ogr culturas.gpkg $DOWNLOADED_SOURCE/culturas.gpkg T111 -limit 100
for layer in T150 Culturas Codes; do
  ogr2ogr -update culturas.gpkg $DOWNLOADED_SOURCE/culturas.gpkg $layer -limit 100
done
```

`Culturas` (empty) and `Codes` (the NUTS 3 code list) are kept in the 2025 file so the layer
filter is exercised on the layers it has to skip.

2020-2022 ship an archive of regional files instead of one GeoPackage, so those fixtures are
zips. Each keeps 100 features per region, plus a few features of a layer the edition's filter
has to skip (`Parcelas*`, `Baldios*`), and 2020/2021 keep a slice of the campaign's crop table
so the join is exercised: enough rows to match most of the sampled fields, a few keys that
match none of them, and — for 2021 — the fourteen rows keyed on `Osa_id = 0` that make the
crop table non-unique.

`Culturas_2021.dbf` is deliberately *not* in the 2021 member list. It has no geometry, and
`DATA_LAYER` matches its name, so a converter that filtered layers by that pattern alone would
convert a 3.4M-row attribute table as if it were field boundaries.

```
for f in Ocupacoes_solo_ALENTEJO Ocupacoes_solo_ALGARVE ... ; do
  ogr2ogr $f.shp $DOWNLOADED_SOURCE/$f.shp -limit 100
done
ogr2ogr -f "ESRI Shapefile" -nlt NONE Culturas_2021.dbf $DOWNLOADED_SOURCE/Culturas_2021.dbf \
  -where "Osa_id IN (<the sampled OSA_IDs>, <a few unmatched keys>, 0)"
zip -9 2021.zip *.shp *.shx *.dbf *.prj *.cpg      # plain deflate, see below
```

## 2017-2019

Same shape as the 2020-2022 fixtures (a zip of regional files), but these editions are
plain shapefiles with one layer each, so the member list is the only thing that decides
what gets read. All ten members of each edition must be present or `get_data` fails on
the missing path, so the uninteresting regions are cut to 20 rows and the budget spent on
the ones that carry a mechanism:

- **2018 `Ocupacoes_solo_Norte_N` and `Ocupacoes_solo_Norte_S`** keep 100 rows each, of
  which **30 share an OSA_ID**. The real edition repeats 154,980 fields between these two
  members, byte for byte, and converting both as published inflates it by that many rows.
  The unique halves deliberately exclude every other shared id, so the fixture overlap is
  exactly 30 and `test_2018_drops_exactly_the_duplicated_rows` can assert the count.
- **2017 `Ocupacoes_solo_RAA` and `Ocupacoes_solo_RAM`** publish no `OSA_ID` at all and
  repeat `PAR_NUM`, so the fixtures are chosen to keep rows whose `PAR_NUM` repeats. They
  exercise the synthesised id on the condition that forced it.
- **2018 `ocupacoes.solo.Norte_N1.2018jun10`** is awkward three ways at once and carries
  all fourteen crop names in which the provider lost an accent to a literal `?`. It is
  also the only member with lowercase, non-contiguous crop columns (`c1..c7`, `c9`, no
  `c8`) and one of two published in EPSG:3763. Note the dots inside the filename.
- **2019 `Ocupacoes_solo_RAA`** keeps 100 rows for its 28 crop columns, and
  **`ocupacoes_solo_n_1`** is the EPSG:3763 case for that year.
- **`Parcelas_*`** is in each zip but in no member list: it is the parcel block geometry,
  not field boundaries. 2019 also keeps an orphan `osas_az_ocidental.qpj` and one of the
  `*.sr.lock` files the provider shipped, so the fixture proves the junk is simply never
  named rather than actively skipped.

The rows were selected from the real archives by these criteria rather than with a plain
`ogr2ogr -limit`, so a regenerated fixture has to keep them for the tests to hold.

## Compression

The real 2017-2022 archives are Deflate64, which python's `zipfile` cannot read. The 2022
fixture is Deflate64 too, recompressed with `python to_deflate64.py 2022.zip`, so the tests
extract the format IFAP publishes; the other fixtures are plain Deflate.
