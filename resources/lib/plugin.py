# -*- coding: utf-8 -*-

import datetime
import os
import pickle
from abc import abstractmethod
from collections import OrderedDict

import urllib2
import xbmc
import xbmcgui
import xbmcplugin
from dateutil.tz import tzlocal, tzoffset, UTC
from urlparse import urlparse

from . import simpleplugin

addon = simpleplugin.Addon()
_ = addon.initialize_gettext()

LISTING_PICKLE = 'listing.pickle'

MSG_NOT_LINKS = 'Stream information will be available 30 minutes prior to the begining of an event.'


def file_read(file):
    with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
        try:
            return f.read()
        except Exception as e:
            print(e)
    return ''


class Plugin(simpleplugin.Plugin):

    def __init__(self):
        super(Plugin, self).__init__()
        self._dir = {'media': os.path.join(self.path, 'resources', 'media'),
                     'font': os.path.join(self.path, 'resources', 'data', 'font'),
                     'lib': os.path.join(self.path, 'resources', 'lib'),
                     'thumb': os.path.join(self.config_dir, 'thumb')}

        if not os.path.exists(self.dir('thumb')):
            os.mkdir(self.dir('thumb'))

        self._site = self.get_setting('url_site')
        self._listing_pickle = os.path.join(self.config_dir, LISTING_PICKLE)
        self.settings_changed = False
        self.stop_update = False

        self._date_scan = None  # Время сканирования в utc
        self._listing = OrderedDict()
        self._language = xbmc.getInfoLabel(
            'System.Language')  # Russian English
        self.load()

    @staticmethod
    def format_timedelta(dt, pref):
        h = int(dt.seconds / 3600)
        return u'{} {} {} {:02} мин.'.format(pref, u'%s дн.' % dt.days if dt.days else u'',
                                             u'%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))

    @staticmethod
    def create_id(key):
        """
        Создаем id для записи
        :param key: str оригинальная для записи строка
        :return: возвращает id
        """
        return hash(key)

    @staticmethod
    def cache_thumb_name(thumb):
        """
        Находит кеш рисунка
        :param thumb:
        :return:
        """
        thumb_cached = xbmc.getCacheThumbName(thumb)
        thumb_cached = thumb_cached.replace('tbn', 'png')
        return os.path.join(os.path.join(xbmc.translatePath("special://thumbnails"), thumb_cached[0], thumb_cached))

    @staticmethod
    def get_path_sopcast(href):
        url = urlparse(href)
        path = "plugin://program.plexus/?mode=2&url=" + url.geturl() + "&name=Sopcast"
        return path

    @staticmethod
    def _get_response_info(response):
        response_info = ['Response info',
                         'Status code: {0}'.format(response.code)]
        if response.code != 200:
            raise Exception('Error (%s) в %s ' %
                            (response.code, response.geturl()))
        response_info.append('URL: {0}'.format(response.geturl()))
        response_info.append('Info: {0}'.format(response.info()))
        return '\n'.join(response_info)

    @abstractmethod
    def _parse_listing(self, html, progress=None):
        """
        Парсим страницу для основного списка
        :param html: страница html
        :return: словарь словарей с данными для формирования списка корневой виртуальной папки
        listing = {
                    id : {
                        id: int,
                        label: '',
                        date: datetime, # должно быть осведомленное время в UTC
                        thumb: '',
                        icon: '',
                        poster: '',
                        fanart: '',
                        url_links: '', # ссылка на web страницу со ссылками на трансляции
                        href: [
                                {
                                'id': int,
                            }
                        ]
                    }
                }

        """
        pass

    @abstractmethod
    def _parse_links(self, html):
        """
        Парсим страницу со ссылками
        :param html: страница html
        :return: список словарей для формирования списка папки со ссылками
        [
            {
                'id': int,
            }
        ]
        """
        pass

    @property
    def date_scan(self):
        return self._date_scan

    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def dir(self, dir_):
        return self._dir[dir_]

    def get(self, id_, key):
        return self._listing[id_][key]

    def load(self):
        try:
            if os.path.exists(self._listing_pickle):
                with open(self._listing_pickle, 'rb') as f:
                    self._date_scan, self._listing = pickle.load(f)
        except Exception as e:
            self.logd('ERROR load', str(e))

    def dump(self):
        with open(self._listing_pickle, 'wb') as f:
            pickle.dump([self.date_scan, self._listing], f)

    def create_listing_(self):
        return self.create_listing(self.get_listing(),
                                   content='movies',
                                #    view_mode=55,
                                #    sort_methods=(
                                #        xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING),
                                   cache_to_disk=False)

    def get_listing(self):
        """
        Список для корневой виртуальной папки.
        :return:
        """
        self.update()
        return self._get_listing()

    def get_links(self, params):
        """
        Список для папки ссылок
        :param params: Передается в self.get_url(action='links', id=item['id'])
        :return:
        """
        id = int(params['id'])
        links = self.links(id, isdump=True)
        self.logd('links', links)

        if not links:
            return [{'label': MSG_NOT_LINKS,
                     'info': {'video': {'title': self._site, 'plot': self._site}},
                     'art': {'icon': self.icon, 'thumb': self.icon, },
                     'url': self.get_url(action='play',
                                         href='https://www.ixbt.com/multimedia/video-methodology/'
                                         'bitrates/avc-1080-25p/1080-25p-10mbps.mp4'),
                     'is_playable': True}]

        return self._get_links(id, links)

    def links(self, id, isdump=False):
        """
        Возвращает список ссылок кокретного элемента. При необходимости парсит по ссылке в элементе.
        :param id: id элемента
        :return:
        """
        links = self.get(id, 'href')
        tnd = self._time_now_date(id)
        tsn = self._time_scan_now()
        dt = self.get_setting('delta_links')

        self.logd('links links', links)
        self.logd('links self.date_scan', self.date_scan)

        if not links or not self.date_scan or tsn > self.get_setting('delta_scan') or (tsn > dt and tnd < dt):
            self.logd('links - id - %s : time now date - %s time scan now - %s' %
                      (id, tnd, tsn), links)
            html = self.http_get(self.get(id, 'url_links'))
            if not html:
                self.logd('links', 'not html')
                return links
            del links[:]
            links.extend(self._parse_links(html))
            if links and isdump:
                self.dump()

        self.logd('self.get(%s, href)' % id, self.get(id, 'href'))

        return links

    def update(self):
        """
        Обновление списков для виртуальных папок, рисунков, удаление мусора, сохранение в pickle
        :return:
        """

        self.logd('plugin.update - self.settings_changed',
                  self.settings_changed)

        if not self.is_update():
            return

        progress = xbmcgui.DialogProgressBG()

        progress.create(self.name, 'ОБНОВЛЕНИЕ ДАННЫХ ...')

        self.log('START UPDATE')

        progress.update(10, message='Загрузка данных сайта')

        #file_html = os.path.join(self.path, 'livesport.html')

        html = self.http_get(self._site)        
        
        # with open(file_html, 'wb') as f:
        #     f.write(html)

        #html = file_read(file_html) 

        self.log('***** 1')

        self._listing = self._parse_listing(html, progress=progress)

        self.log('***** 2')

        if not self._listing:
            self.logd('update', 'self._listing None')
            return

        # if self.get_setting('is_noold_item'):
        #     for id in self._listing.keys():
        #         dt = self._time_now_date(id)
        #         if dt < -180:
        #             del self._listing[id]

        for item in self._listing.values():
            if 'thumb' not in item:
                item['thumb'] = ''
            if 'icon' not in item:
                item['icon'] = ''
            if 'poster' not in item:
                item['poster'] = ''
            if 'fanart' not in item:
                item['fanart'] = ''
            if 'url_links' not in item:
                item['url_links'] = ''
            if 'href' not in item:
                item['href'] = []

        self.log('***** 3')

        if self.get_setting('is_pars_links'):
            percent = 60
            i = (40 // len(self._listing)) if len(self._listing) else 2
            for val in self._listing.values():
                percent += i
                progress.update(percent, '%s: cканирование ссылок' %
                                self.name, val['label'])
                self.links(val['id'], isdump=False)

        self.log('***** 4')

        artwork = []
        for item in self._listing.values():
            if item['thumb']:
                artwork.append(item['thumb'])
            if item['icon']:
                artwork.append(item['icon'])
            if item['poster']:
                artwork.append(item['poster'])
            if item['fanart']:
                artwork.append(item['fanart'])

        for file in os.listdir(self.dir('thumb')):
            f = os.path.join(self.dir('thumb'), file)
            if f not in artwork:
                self.remove_thumb(f)

        self.log('***** 5')

        self._listing = OrderedDict(
            sorted(self._listing.items(), key=lambda t: t[1]['date']))

        self._date_scan = self.time_now_utc()
        self.dump()
        self.log('STOP UPDATE')
        progress.update(100, self.name, 'Завершение обновлений...')
        xbmc.sleep(500)

        self.log('***** 6')

        progress.close()

    def is_update(self):
        """
        Проверяет необходимость обновления списков
        :return: True - обновляем, False - нет
        """
        try:
            if not self.date_scan:
                self.logd('is_update', 'True - not self.date_scan')
                return True
            if self.settings_changed:
                self.logd('is_update', 'True - self.settings_changed')
                return True
            if not os.path.exists(self._listing_pickle):
                self.logd(
                    'is_update', 'True - not os.path.exists(self._listing_pickle)')
                return True
            if not self._listing:
                self.logd('is_update', 'True - not self._listing')
                return True
            if self._time_scan_now() > self.get_setting('delta_scan'):
                self.logd(
                    'is_update', 'True - self._time_scan_now() > self.get_setting(delta_scan)')
                return True  #
        except Exception as e:
            self.logd('ERROR -> is_update', e)
            return True
        self.logd('is_update', 'False')
        return False

    def play(self, params):
        """
        Воспроизводит ссылку
        :param params: Передается в self.get_url(action='play', href=href, id=item['id']) и
                                    self.get_url(action='play', href=link['href'], id=id
        :return:
        """
        path = ''
        msg = ''

        self.logd('play', params)
        if 'href' not in params or not params['href']:
            links = self.links(int(params['id']), isdump=True)
            self.logd('play links', links)
            for h in links:
                if h['title'] == self.get_setting('play_engine').decode('utf-8'):
                    params['href'] = h['href']
                    break
            if 'href' not in params or not params['href']:
                msg = 'НЕТ ССЫЛОК НА ТРАНСЛЯЦИЮ МАТЧА!'
                self.logd('play', msg)
                xbmcgui.Dialog().notification(self.name, msg, self.icon, 500)
                return None

        href = params['href']
        url = urlparse(href)
        if url.scheme == 'acestream':
            path = self.get_path_acestream(href)
            if not path:
                return None
            try:
                if urlparse(path).port == 6878:
                    progress = xbmcgui.DialogProgressBG()
                    progress.create('Ace Stream Engine', self.name)

                    self.log('start acestream play')

                    as_url = 'http://' + '127.0.0.1' + ':' + '6878' + '/ace/getstream?id=' + \
                        urlparse(href).netloc + \
                        "&format=json"  # &_idx=" + str(ep)

                    json = eval(self.http_get(as_url).replace(
                        'null', '"null"'))["response"]
                    self.log(type(json))
                    self.log(json)
                    stat_url = json["stat_url"]
                    self.logd('stat_url', stat_url)
                    stop_url = json["command_url"] + '?method=stop'
                    self.logd('stop_url', stop_url)
                    purl = json["playback_url"]
                    self.logd('purl', purl)

                    for i in range(30):
                        xbmc.sleep(1000)
                        j = eval(self.http_get(stat_url).replace(
                            'null', '"null"'))["response"]
                        if j == {}:
                            progress.update(i*3, message=u'ожидание...')
                        else:

                            status = j['status']
                            if status == 'dl':
                                progress.update(
                                    i*3,  message=u'воспроизведение...')
                                xbmc.sleep(1000)
                                break
                            progress.update(i*3, message=u'пребуферизация...')
                            self.logd('get stat acestream - ', j)
                            msg = 'seeds - %s speed - %s download - %s' % (
                                str(j['peers']), str(j['speed_down']), str(j['downloaded']/1024))
                            progress.update(i*3, msg)

                    if i == 29:
                        xbmcgui.Dialog().notification(self.name, 'Torrent not available or invalid!', self.icon, 500)
                        self.http_get(stop_url)

                    progress.close()
                    xbmc.sleep(1000)
                    path = purl
            except Exception as e:
                xbmcgui.Dialog().notification(
                    self.name, 'Torrent not available or invalid!', self.icon, 500)
                self.logd('error acestream (%s)' %
                          str(e), 'Torrent not available or invalid!')
                if progress:
                    progress.close()
                return None

        elif url.scheme == 'sop':
            path = self.get_path_sopcast(href)
        else:
            path = url.geturl()

        if not path:
            msg = 'ПУСТОЙ ПУТЬ НА ТРАНСЛЯЦИЮ МАТЧА!'
            xbmcgui.Dialog().notification(self.name, msg, self.icon, 500)
            self.logd('play', msg)
            return None

        self.logd('play', 'PATH PLAY: %s' % path)

        return self.resolve_url(path, succeeded=True)

    @staticmethod
    def time_now_utc():
        """
        Возвращает текущее осведомленное(aware) время в UTC
        :return:
        """
        return datetime.datetime.now(tz=UTC)

    @staticmethod
    def time_to_local(dt):
        """
        Переводит осведомленное (aware) время в локальное осведомленное
        :param dt: осведомленное (aware) время
        :return: локальное осведомленное (aware)
        """
        return dt.astimezone(tzlocal())

    def _time_naive_site_to_local_aware(self, dt):
        """
        Переводит наивное время из сайта в осведомленное (aware) локальное время
        :param dt: datetime относительное (naive) время из результатов парсинга сайта
        :return: datetime локальное осведомленное (aware) время
        """
        tz = tzoffset(None, int(self.get_setting('time_zone_site')) * 3600)
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(tzlocal())

    def _time_naive_site_to_utc_aware(self, dt):
        """
        Переводит наивное время из сайта в осведомленное (aware) время UTC
        :param dt: datetime относительное (naive) время из результатов парсинга сайта
        :return: datetime UTC осведомленное (aware) время
        """
        tz = tzoffset(None, int(self.get_setting('time_zone_site')) * 3600)
        dt = dt.replace(tzinfo=tz)
        return dt.astimezone(UTC)

    def _time_now_date(self, id):
        """
        Время в минутах от текущего времени до даты в элементе списка. Если матча с таким id нет, возвращаем None
        """
        if id not in self._listing:
            return None

        return int((self.get(id, 'date') - self.time_now_utc()).total_seconds() / 60)

    def _time_scan_now(self):
        """
        Время в минутах от последнего сканирования до текущего времени
        """
        if self.date_scan is None:
            return None
        return int((self.time_now_utc() - self.date_scan).total_seconds() / 60)

    def _time_scan_date(self, id):
        """
        Время в минутах от последнего сканирования до даты в элементе списка. Если матча с таким id нет, возвращаем None
        """
        if self.date_scan is None:
            return None
        return int((self.get(id, 'date') - self.date_scan).total_seconds() / 60)

    def http_get(self, url):
        try:
            req = urllib2.Request(url=url)
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                           ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                           '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')

            response = urllib2.urlopen(req)
            self.log(self._get_response_info(response))
            html = response.read()
            response.close()
            return html
        except Exception as e:
            # xbmcgui.Dialog().notification(self.name, 'HTTP ERROR %s' % str(e),
            #                             xbmcgui.NOTIFICATION_ERROR, 2000)
            err = '*** HTTP ERROR: %s ' % str(e)
            self.log(err)
            return ''

    def remove_thumb(self, thumb):
        """
        Удаляет рисунок и кеш
        :param thumb: 
        :return: 
        """
        if os.path.exists(thumb):
            self.logd('remove_thumb', thumb)
            os.remove(thumb)
        self.remove_cache_thumb(thumb)

    def remove_cache_thumb(self, thumb):
        """
        Удаляет кеш рисунка
        :param thumb: 
        :return: 
        """
        if self.cache_thumb_name:
            thumb_cache = self.cache_thumb_name(thumb)
            self.logd('remove_cache_thumb', thumb_cache)
            if os.path.exists(thumb_cache):
                os.remove(thumb_cache)

    def remove_all(self):
        """

        :return: 
        """
        pics = os.listdir(self.dir('thumb'))
        for pic in pics:
            pic = os.path.join(self.dir('thumb'), pic)
            self.remove_thumb(pic)
        # fs = os.listdir(self.config_dir)
        # for f in fs:
        #     if f != 'settings.xml' and f != 'thumb' and f != '__gettext__.pcl':
        #         f = os.path.join(self.config_dir, f)
        #         os.remove(f)

    def get_path_acestream(self, href):
        """
        В зависимости от настроек формирует путь для воспроизведения acestream
        :param href: acestream://132121321321321321321321
        :return:
        """
        path = ''
        item = 0
        url = urlparse(href)
        if self.get_setting('is_default_ace'):
            item = self.get_setting('default_ace')
        else:
            dialog = xbmcgui.Dialog()
            list = [
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting(
                    'is_hls1') else '', self.get_setting('ipace1')),
                'ACESTREAM %s [%s]' % ('hls' if self.get_setting(
                    'is_hls2') else '', self.get_setting('ipace2')),
                'HTTPAceProxy [%s]' % self.get_setting('ipproxy'),
                'Add-on TAM [127.0.0.1]',
                'Add-on Plexus']

            if self.version_kodi < 17:
                item = dialog.select(
                    'Выбор способа воспроизведения Ace Straem', list=list)
            else:
                item = dialog.contextmenu(list)

            if item == -1:
                return None

        cid = url.netloc

        if item == 0:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                self.get_setting('ipace1'), 'manifest.m3u8' if self.get_setting(
                    'is_hls1') else 'getstream', cid)
        elif item == 1:
            path = 'http://%s:6878/ace/%s?id=%s' % (
                self.get_setting('ipace2'), 'manifest.m3u8' if self.get_setting(
                    'is_hls2') else 'getstream', cid)
        elif item == 2:
            path = "http://%s:8000/pid/%s/stream.mp4" % (
                self.get_setting('ipproxy'), cid)
        elif item == 3:
            path = "plugin://plugin.video.tam/?mode=play&url=%s&engine=ace_proxy" % href
        elif item == 4:
            path = "plugin://program.plexus/?mode=1&url=" + \
                url.geturl() + "&name=My+acestream+channel"

        return path

    def on_settings_changed(self):
        self.settings_changed = True
        xbmcgui.Dialog().notification(
            self.name, 'Изменение настроек !', xbmcgui.NOTIFICATION_INFO, 500)
        self.update()
        self.settings_changed = False
        # xbmc.executebuiltin('Dialog.Close(all,true)')

    def reset(self):
        """
        Сброс списков
        :return:
        """
        xbmcgui.Dialog().notification(
            self.name, 'Обновление данных плагина', self.icon, 500)
        self.log('START RESET')
        self.remove_all()
        self.update()
        self.log('END RESET')
        # xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.executebuiltin('Container.Refresh()')

    def geturl_isfolder_isplay(self, id, href):
        """

        :param id:
        :param href:
        :return:
        """
        is_folder = True
        is_playable = False
        get_url = self.get_url(action='links', id=id)

        if self.get_setting('is_play'):
            is_folder = False
            is_playable = True
            get_url = self.get_url(action='play', href=href, id=id)

        return is_folder, is_playable, get_url

    def is_create_artwork(self):
        if self.get_setting('is_thumb') or self.get_setting('is_fanart') or self.get_setting('is_poster'):
            return True
        return False
