from .registry import Registry

if __name__ == Registry.src_package or __name__ == "__main__":
    import click

    @click.group()
    @click.version_option(version=Registry.get_version(), prog_name=Registry.cli_title)
    def fiboa_cli():
        pass

    commands = Registry.get_commands()
    for command in commands:
        click_cmd = command.get_cli_command(command)
        click_args = command.get_cli_args().values()
        for arg in click_args:
            click_cmd = arg(click_cmd)
        fiboa_cli.add_command(click_cmd)
