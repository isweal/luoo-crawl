import os

DOWNLOAD_DIR = os.path.abspath(os.path.dirname(__file__)) + '/song'

if not os.path.isdir(DOWNLOAD_DIR):
    os.mkdir(DOWNLOAD_DIR)
