from .ch_base import OPEN, SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch"
    short_name = "Switzerland"
    title = "Field boundaries for Switzerland"
    description = """
The agricultural usage areas (Nutzungsflächen) of every canton that publishes them openly on
geodienste.ch, in their current state. The cantons' terms of use differ; the ch_<canton>
converters state them per canton, and three cantons (ZH, GE, SZ) also have earlier years there.
    """
    license = "opendata.swiss terms: Open use. Must provide the source. <https://opendata.swiss/terms-of-use#terms_by>"
    attribution = f"Kantone, via geodienste.ch (KGK-CGC) — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"

    def get_urls(self):
        urls = {}
        for service in self.get_services():
            if service["publication_data"] != OPEN:
                self.info(f"Skipping canton {service['canton']}: {service['publication_data']}")
                continue
            urls[self.get_geopackage_url(service)] = ["geopackage/*.gpkg"]
        return urls
