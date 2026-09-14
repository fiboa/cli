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
zip -9 2021.zip *.shp *.shx *.dbf *.prj *.cpg      # plain deflate: the source archives are
                                                    # Deflate64, which python's zipfile refuses
```
