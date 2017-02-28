import re


def get_colon_after(text):
    return re.search(r"(?<=: ).*", text).group()


def index_add_zero(i):
    return str(i) if i >= 10 else '0' + str(i)


def index_none(i):
    return str(i)
