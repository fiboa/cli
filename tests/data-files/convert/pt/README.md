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
