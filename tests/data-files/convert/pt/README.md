The gpkg is built up out of multiple layers, only the 'Culturas_'-prefixed layers should be loaded

The test file is created by taking the first 100 features from these different layers. 
We now have a representable test-case. Downloaded data is assumed in $DOWNLOADED_SOURCE/Continente.gpkg. Run

```
ogr2ogr Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg Continente -limit 100
ogr2ogr -update Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg Culturas_Aveiro -limit 100
ogr2ogr -update Continente.gpkg $DOWNLOADED_SOURCE/Continente.gpkg OcupacoesSolo_Aveiro -limit 100
```
