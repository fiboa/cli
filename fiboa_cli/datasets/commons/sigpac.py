import re

import requests

HUB = "https://sigpac-hubcloud.es"


class SigpacRecintoMixin:
    """The SIGPAC recintos, which FEGA publishes per province for the whole country.

    A region that publishes the same register itself is preferable, but not every
    regional portal is reachable; this is the same data from the paying agency.
    """

    # the two-digit province codes the region covers
    provinces: tuple[str, ...] = ()
    variants = {year: year for year in ("2026", "2025")}

    use_code_attribute = "uso_sigpac"
    # dn_surface is in square metres: median 2,340, largest 8.5 million
    area_is_in_ha = False
    use_variant_as_determination = True

    def get_urls(self):
        listing = requests.get(f"{HUB}/geopackages/{self.variant}/recintos/", timeout=120)
        listing.raise_for_status()
        paths = re.findall(r'HREF="(/geopackages/[^"]+\.zip)"', listing.text)
        wanted = {p for p in paths if p.rsplit("/", 1)[-1][:2] in self.provinces}
        found = {p.rsplit("/", 1)[-1][:2] for p in wanted}
        if found != set(self.provinces):
            raise ValueError(
                f"{self.variant} has no recintos for province(s) {sorted(set(self.provinces) - found)}"
            )
        return {f"{HUB}{p}": ["*.gpkg"] for p in sorted(wanted)}

    def layer_filter(self, layer, uri):
        # the archive also holds the code lists the register refers to
        return layer == "recinto"

    def migrate(self, gdf):
        # the base converter splits multi-part geometries after it has checked the ids
        gdf = self.split_multipart(gdf)

        # The register has no row identifier; the cadastral key is one, and it is what
        # es.py builds for the declared crops of the same parcels.
        def part(column):
            return gdf[column].astype("Int64").astype(str)

        gdf["id"] = (
            part("provincia").str.zfill(2)
            + "-"
            + part("municipio")
            + "-"
            + part("agregado")
            + "-"
            + part("zona")
            + "-"
            + part("poligono")
            + "-"
            + part("parcela")
            + "-"
            + part("recinto")
        )
        # a recinto can be several polygons, and then its key is not enough on its own
        piece = gdf.groupby("id").cumcount()
        gdf.loc[piece > 0, "id"] += "-" + (piece[piece > 0] + 1).astype(str)
        return super().migrate(gdf)
