import threading
import time
import sys
import os
import multiprocessing
import urllib.request, urllib.parse, urllib.error
from queue import Queue
from fake_useragent import UserAgent
from selenium import webdriver
from bs4 import BeautifulSoup
from random import randrange
from .utils.message import notice, error, success
from .utils.tools import *
from settings import DOWNLOAD_DIR
from .main import db


class LuooSpider(object):
    def __init__(self):
        self.headers = {
            'Connection': 'Keep-Alive',
            'Accept': 'text/html, application/xhtml+xml, */*',
            'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'User-Agent': None
        }
        self.base_url = 'http://www.luoo.net/music'

    def __driver_setup(self, url):
        ua = UserAgent()
        self.headers['User-Agent'] = ua.random
        driver = webdriver.PhantomJS('/usr/local/bin/phantomjs')
        driver.set_window_size(1024, 2000)
        driver.get(url)
        driver.implicitly_wait(randrange(1, 3))
        return driver.page_source

    def __crawl_newest(self):
        data = self.__driver_setup(self.base_url)
        soup = BeautifulSoup(data, "html.parser")
        vol_url = soup.select_one("div.vol-list a").get('href')
        max_vol = vol_url[(vol_url.rfind('/') + 1):]
        return max_vol

    def __craw_vol(self, vol_id, write=False, download=None):
        if write:
            items = db.vol.find({'vol_id': vol_id})
            if items.count() > 0:
                notice("vol {} already exists.".format(vol_id))
                if download:
                    songs = items[0]['songs']
                    download.push_queue(songs)
                return

        data = self.__driver_setup(self.base_url + '/' + str(vol_id))
        soup = BeautifulSoup(data, "html.parser")
        vol_dic = {}
        try:
            vol_dic['vol_id'] = vol_id
            vol_dic['title'] = soup.find('span', 'vol-title').text
            vol_dic['img'] = soup.find('img', 'vol-cover').get('src')
            vol_dic['info'] = soup.find('div', 'vol-desc').text.strip()
            vol_dic['tags'] = ','.join([tag.text for tag in soup.find_all('a', 'vol-tag-item')])
            songs = []
            song_path = soup.find_all('div', 'player-wrapper')
            for i, h in enumerate(song_path):
                song = dict()
                song['vol_id'] = vol_id
                song['vol_name'] = vol_dic['title']
                song['index'] = i + 1
                song['img'] = h.find('img').get('src')
                song['name'] = h.find('p', 'name').text
                song['artist'] = get_colon_after(h.find('p', 'artist').text)
                song['album'] = get_colon_after(h.find('p', 'album').text)
                song['url'] = 'http://mp3-cdn.luoo.net/low/luoo/radio{}/%s.mp3'.format(vol_id)
                songs.append(song)
            vol_dic['songs'] = songs
            if write:
                db.vol.insert_one(vol_dic)
            success('vol {} is loaded.'.format(vol_id))
            if download:
                download.push_queue(songs)

        except:
            error('vol ' + str(vol_id) + ' not exit!')

    @property
    def max_vol(self):
        notice('get max vol..')
        return self.__crawl_newest()

    def get_vol(self, vol_id, write=False, download=None):
        notice('get vol ' + str(vol_id))
        return self.__craw_vol(vol_id, write, download)


class LuooThread(threading.Thread):
    def __init__(self, queue, sleep_time):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sleep_time = sleep_time

    def run(self):
        while True:
            if not self.queue.empty():
                work = self.queue.get()
                LuooSpider().get_vol(work[0], work[1], work[2])
                self.queue.task_done()
                time.sleep(self.sleep_time)
            else:
                time.sleep(1)


class LuooLoader(object):
    def __init__(self):
        self.__queue = Queue()
        self.__workerAmount = 3
        # self.__workerAmount = multiprocessing.cpu_count() * 2 + 1
        self.__workerPool = []

    def work(self, write=False, download=True):
        try:
            max_vol = LuooSpider().max_vol

            dw = None
            if download:
                dw = SongLoader()

            for i in range(1, int(max_vol) + 1):
                self.__queue.put((i, write, dw))

            for i in range(self.__workerAmount):
                self.__workerPool.append(LuooThread(self.__queue, randrange(0, 2)))

        except ValueError:
            error('max_vol error')
            return

        for worker in self.__workerPool:
            if not worker.isDaemon():
                worker.setDaemon(True)
                worker.start()
        self.__queue.join()


class SongDownloader(object):
    def get_song(self, url, dir_name, name):
        dir_relate = "{}/{}".format(DOWNLOAD_DIR, dir_name)
        relate = "{}/{}".format(dir_relate, name + url[url.rfind('.'):])
        if os.path.isfile(relate):
            # notice('the song {} already exists.'.format(name))
            return

        if not os.path.isdir(dir_relate):
            os.mkdir(dir_relate)

        def reporthook(a, b, c):
            if c > 1000000:
                per = (100 * a * b) / c
                if per >= 100:
                    success(name + ' Done..')
                    sys.stdout.flush()

        try:
            urllib.request.urlretrieve(url, relate, reporthook)
        except urllib.error.HTTPError as e:
            pass


class SongLoader(object):
    def __init__(self):
        self.__queue = Queue()
        self.__workerAmount = 1
        self.__workerPool = []
        self.song_list = []
        self.work()

    def push_queue(self, song_list):
        self.song_list.extend(song_list)
        for i, e in enumerate(self.song_list):
            url_none = e['url'] % index_none(e['index'])
            url_zero = e['url'] % index_add_zero(e['index'])
            dir_name = str(e['vol_id']) + '-' + e['vol_name']
            self.__queue.put((url_none, dir_name, e['name']))
            self.__queue.put((url_zero, dir_name, e['name']))

    def work(self):
        for i in range(self.__workerAmount):
            self.__workerPool.append(SongThread(self.__queue, randrange(0, 2)))

        for worker in self.__workerPool:
            if not worker.isDaemon():
                worker.setDaemon(True)
                worker.start()
        self.__queue.join()


class SongThread(threading.Thread):
    def __init__(self, queue, sleep_time):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sleep_time = sleep_time

    def run(self):
        while True:
            if not self.queue.empty():
                work = self.queue.get()
                SongDownloader().get_song(work[0], work[1], work[2])
                self.queue.task_done()
                time.sleep(self.sleep_time)
            else:
                time.sleep(1)
