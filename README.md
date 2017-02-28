## luoo-crawl

a simple spider for [luoo](http://www.luoo.net) to get the vol info and download the music.
> python 3.5 is required

### Usage

```bash
$ python run.py --vol 1
```

```python
"""
Usage: run.py [OPTIONS]

Options:
  --vol TEXT                  the vol id you want to load.
  --write / --no-write        do you want to write vol to mongodb?
  --download / --no-download  do you want to download the song?
  --help                      Show this message and exit.

"""
@click.command()
@click.option('--vol', help='the vol id you want to load.', default='all')
@click.option('--write/--no-write', help='do you want to write vol to mongodb?', default=False)
@click.option('--download/--no-download', help='do you want to download the song?', default=True)
```

### Todo

- [ ] improve the console print.