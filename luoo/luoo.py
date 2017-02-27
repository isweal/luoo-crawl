import threading
import time
import multiprocessing
from queue import Queue
from fake_useragent import UserAgent
from selenium import webdriver
from bs4 import BeautifulSoup
from random import randrange
from .utils.message import notice
from .utils.regTool import get_colon_after


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

    def __craw_vol(self, vol_id):
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
        except:
            print('vol ' + str(vol_id) + ' not exit!')
            return {}

        return vol_dic

    @property
    def max_vol(self):
        notice('get max vol..')
        return self.__crawl_newest()

    def get_vol(self, vol_id):
        notice('get vol ' + str(vol_id))
        return self.__craw_vol(vol_id)


class LuooThread(threading.Thread):
    def __init__(self, queue, sleep_time):
        threading.Thread.__init__(self)
        self.queue = queue
        self.sleep_time = sleep_time

    def run(self):
        while True:
            if not self.queue.empty():
                work = self.queue.get()
                result = LuooSpider().get_vol(work[0])
                print("{} - {}".format(work[0], result))
                self.queue.task_done()
                time.sleep(self.sleep_time)
            else:
                time.sleep(1)


class LuooLoader(object):
    def __init__(self):
        self.__queue = Queue()
        self.__workerAmount = multiprocessing.cpu_count() * 2 + 1
        self.__workerPool = []
        self.__build()

    def __build(self):
        try:
            max_vol = LuooSpider().max_vol

            for i in range(1, int(max_vol) + 1):
                self.__queue.put((i,))

            for i in range(self.__workerAmount):
                self.__workerPool.append(LuooThread(self.__queue, 0))

        except:
            pass

    def work(self):
        for worker in self.__workerPool:
            if not worker.isDaemon():
                worker.setDaemon(True)
                worker.start()
        self.__queue.join()
