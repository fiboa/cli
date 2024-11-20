from .dictobject import DictObject

def add_admin(base, country, subdivision = None):
    """
    Add admin columns to the dataset.
    """
    if isinstance(base, dict):
        base = DictObject(base)

    extensions = base.EXTENSIONS.copy() if hasattr(base, 'EXTENSIONS') else []
    extensions.append("https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml")

    columns = base.COLUMNS.copy()
    add_columns = base.ADD_COLUMNS.copy() if hasattr(base, 'ADD_COLUMNS') else {}

    columns["admin:country_code"] = "admin:country_code"
    add_columns["admin:country_code"] = country

    if subdivision is not None:
        columns["admin:subdivision_code"] = "admin:subdivision_code"
        add_columns["admin:subdivision_code"] = subdivision

    return columns, add_columns, extensions
