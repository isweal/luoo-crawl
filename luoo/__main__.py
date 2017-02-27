import click
from .utils.message import error
from .luoo import LuooSpider, LuooLoader


@click.command()
@click.option('--vol', prompt='the vol id you want load, default is all', default='all')
@click.option('--download/--no-download', default=True)
def main(vol, download):
    if vol != 'all':
        try:
            vol = int(vol)
            result = LuooSpider().get_vol(vol)
            print("{} - {}".format(vol, result))
        except:
            error("not correct vol")
    else:
        LuooLoader().work()
    exit(0)


if __name__ == '__main__':
    main()
