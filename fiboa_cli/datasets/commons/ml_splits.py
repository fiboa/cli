class MlSplitsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.id = self.id + "_ml"
        self.title += " with splits"
        self.short_name += " with splits"

        self.columns["split"] = "split"

        if "required" not in self.missing_schemas:
            self.missing_schemas["required"] = []
        self.missing_schemas["required"].append("split")
        if "properties" not in self.missing_schemas:
            self.missing_schemas["properties"] = {}
        self.missing_schemas["properties"]["split"] = {
            "type": "string",
            "enum": ["train", "val", "test"],
        }
