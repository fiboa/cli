from vecorel_cli.encoding.geoparquet import GeoParquet

class FiboaGeoParquet(GeoParquet):

    def __init__(self, file: Union[Path, URL, str]):
        super().__init__(file)