EXTENSIONS = ["https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"]
ADD_COLUMNS = {
    # https://www.euskadi.eus/contenidos/informacion/pac2015_pagosdirectos/es_def/adjuntos/Anexos_PAC_marzo2015.pdf
    # https://www.fega.gob.es/sites/default/files/files/document/AD-CIRCULAR_2-2021_EE98293_SIGC2021.PDF
    # Very generic list
    "crop:code_list": "https://github.com/fiboa/cli/blob/main/fiboa_cli/datasets/data-files/es_coda_uso.csv",
}

def code_filter(col):
    return ~col.isin("AG/CA/ED/FO/IM/IS/IV/TH/ZC/ZU/ZV".split("/"))

