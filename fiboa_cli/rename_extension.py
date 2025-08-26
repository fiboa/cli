from vecorel_cli.rename_extension import RenameExtension


class RenameFiboaExtension(RenameExtension):
    template_org: str = "fiboa"
    template_domain: str = "fiboa.org"

    @staticmethod
    def get_cli_callback(cmd):
        def callback(folder, title, slug, org, prefix):
            return RenameFiboaExtension(title, slug, org, prefix).run(folder=folder)

        return callback
