import os

import geopandas

from fiboa_cli import log


def gml_assure_columns(data, path, uri, layer, **kwargs):
    # if GDAL opens a GML file, it generates a gfs file in which it tries to 'guess' a
    # mapping from the GML XML file to features. This is not always correct.
    # Call this function to add additional attributes from the GML
    # We modify the GFS file, a more elegant solution is preferred
    # See https://gdal.org/en/latest/drivers/vector/gml.html#schema for more info

    if next(iter(kwargs)) not in data.columns:
        log("Patching generated GFS file", "info")
        assert path.endswith(".gml"), "Expected a gml file"
        gfs_file = path[:-4] + ".gfs"
        assert os.path.exists(gfs_file), "Expected a local, generated GFS file by OGR-GML driver"
        # Fix GFS template file
        with open(gfs_file, mode="r") as file:
            gfs_xml = file.read()

        for property in kwargs:
            assert f"<Name>{property}</Name>" not in gfs_xml, "Expected unpatched gfs file"

        lines = gfs_xml.splitlines()
        for property, elements in kwargs.items():
            element_str = "\n".join(f"<{k}>{v}</{k}>" for k, v in elements.items())
            lines.insert(-2, f"<PropertyDefn><Name>{property}</Name>{element_str}</PropertyDefn>")
        with open(gfs_file, mode="w") as file:
            file.write("\n".join(lines))

        data = geopandas.read_file(path, layer=layer)
    return data
