import re


def get_colon_after(text):
    return re.search(r"(?<=: ).*", text).group()
