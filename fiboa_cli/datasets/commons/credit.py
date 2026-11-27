from vecorel_cli.vecorel.util import parse_link_str


def credit_redistributor(converter, name: str, url: str):
    """
    Credits a project that redistributes a national dataset (e.g. EuroCrops) in the
    attribution and the description. The provider stays the national one, as it holds a
    single name and link.
    """
    source = converter.attribution
    if not source and converter.provider:
        source = parse_link_str(converter.provider)[0]
    converter.attribution = f"{source}; {name}" if source else name
    converter.description = f"{converter.description.strip()}\n\n{name}: {url}"
