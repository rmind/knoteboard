import click

from knoteboard.app import App


@click.command()
@click.argument("path", required=False, type=click.Path())
def main(path: str | None = None):
    App(path).run()


if __name__ == "__main__":
    main()
