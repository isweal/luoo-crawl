import click

db = None
client = None

from .utils.message import error
from .luoo import LuooSpider, LuooLoader, SongLoader


@click.command()
@click.option('--vol', help='the vol id you want to load.', default='all')
@click.option('--write/--no-write', help='do you want to write vol to mongodb?', default=False)
@click.option('--download/--no-download', help='do you want to download the song?', default=True)
def main(vol, write, download):
    if write:
        from pymongo import MongoClient
        global db, client
        client = MongoClient()
        db = client.luoo
    if vol != 'all':
        try:
            vol = int(vol)
            LuooSpider().get_vol(vol, write, SongLoader() if download else None)
        except:
            error("not correct vol")
    else:
        LuooLoader().work(write, download)
    if write:
        client.close()
    exit(0)


if __name__ == '__main__':
    main()
