from vecorel_cli.conversion.admin import AdminConverterMixin

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


class IndiaConverter(AdminConverterMixin, FiboaBaseConverter):
    area_is_in_ha = False
    sources = {"https://zenodo.org/api/records/7315090/files-archive": "india_10k.zip"}
    id = "in_10k"
    short_name = "India 10k"
    title = "10,000 Crop Field Boundaries across India"
    description = """
      Release of dataset and neural network weights accompanying the paper
      "Unlocking large-scale crop field delineation in smallholder farming systems with transfer learning and weak supervision"
      (forthcoming in Remote Sensing). Ten thousand crop fields in India were delineated manually through inspection
      of high-resolution satellite imagery (Airbus SPOT). We also provide the weights of the highest performing
      neural network (FracTAL ResUNet architecture) pre-trained in France and fine-tuned on Airbus SPOT images in India.
      The model was trained in MXNet 1.6.0 and can be loaded with the "model.load_parameters()" function.
    """
    index_as_id = True
    providers = [
        {
            "name": "Zenodo",
            "url": "https://zenodo.org/",
            "roles": ["licensor", "producer"],
        }
    ]
    attribution = "https://doi.org/10.5281/zenodo.7315090"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "area": "metrics:area",
    }
    column_additions = {"determination:datetime": "2022-11-12T00:00:00Z"}
