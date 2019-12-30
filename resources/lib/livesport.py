# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library

standard_library.install_aliases()
import urllib.parse
import urllib.error
import urllib.request
# import requests
from . import simpleplugin, makeart
import xbmcgui
import xbmc
from dateutil.tz import UTC, tzlocal, tzoffset
from dateutil.parser import *
import dateutil
import bs4
from urllib.parse import urlparse
from collections import OrderedDict
import pickle
import os
import json
import datetime
from builtins import range
from builtins import str

LISTING_PICKLE = 'listing.pickle'

URL_NOT_LINKS = 'https://www.ixbt.com/multimedia/video-methodology/bitrates/avc-1080-25p/1080-25p-10mbps.mp4'


def file_read(file):
    with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
        try:
            return f.read()
        except Exception as e:
            print(e)
    return ''


class LiveSport(simpleplugin.Plugin):

    def __init__(self):
        super(LiveSport, self).__init__()
        self._dir = {'media': os.path.join(self.path, 'resources', 'media'),
                     'font': os.path.join(self.path, 'resources', 'data', 'font'),
                     'lib': os.path.join(self.path, 'resources', 'lib'),
                     'thumb': os.path.join(self.profile_dir, 'thumb')}

        if not os.path.exists(self.dir('thumb')):
            os.mkdir(self.dir('thumb'))

        self._site = self.get_setting('url_site')
        self._listing_pickle = os.path.join(self.profile_dir, LISTING_PICKLE)
        self.settings_changed = False
        self.stop_update = False

        self._date_scan = None  # Время сканирования в utc
        self._listing = OrderedDict()
        self._language = xbmc.getInfoLabel('System.Language')  # Russian English

        if self._language != 'Russian':
            self._site = os.path.join(self.get_setting('url_site'), 'en')
        else:
            self._site = self.get_setting('url_site')
        global _

        self.load()



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

    def http_get(self, url):
        try:
            req = urllib.request.Request(url=url)
            req.add_header('User-Agent',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                           ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                           '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)')

            response = urllib.request.urlopen(req, timeout=5)
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

        links = self.get(id, 'href')

        self.logd('links links', links)

        status = self.get(id, 'status')

        if links and status == 'OFFLINE':
            self.logd('links', 'id - %s  status - %s ' % (id, status))
            return links
        if not links or not self.date_scan or tsn > self.get_setting('delta_scan') or tsn > dt:  # and tnd < dt):
            self.logd('links - id - %s : time now date - %s time scan now - %s' %
                      (id, tnd, tsn), links)
            html = self.http_get(self.get(id, 'url_links'))
            if not html:
                self.logd('links', 'not html')
                return links
            del links[:]
            links.extend(self._parse_links(id, html))
            #    if links and status == 'OFFLINE':
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

        progress.create(self.name, _('UPDATE DATA ...'))

        self.log('START UPDATE')

        progress.update(1, message=_('Loading site data ...'))

        # file_html = os.path.join(self.path, 'livesport.html')

        # import web_pdb
        # web_pdb.set_trace()

        html = self.http_get(self._site)

        # self.log(html)

        # with open(file_html, 'wb') as f:
        #     f.write(html)

        # html = file_read(file_html)

        self.log('***** 1')

        self._listing = self._parse_listing(html, progress=progress)

        self.log('***** 2')

        if not self._listing:
            self.logd('update', 'self._listing None')
            return

        for item in list(self._listing.values()):
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

        # if self.get_setting('is_pars_links'):
        #     percent = 60
        #     i = (40 // len(self._listing)) if len(self._listing) else 2
        #     for val in self._listing.values():
        #         percent += i
        #         progress.update(percent, '%s: %s' %
        #                         (_('link scanning'), self.name), val['label'])
        #         self.links(val['id'], isdump=False)

        self.log('***** 4')

        artwork = []
        for item in list(self._listing.values()):
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
            sorted(list(self._listing.items()), key=lambda t: t[1]['date']))

        self._date_scan = self.time_now_utc()
        self.dump()
        self.log('STOP UPDATE')
        progress.update(100, self.name, _('End update...'))
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

        # self.logd('play', params)
        # if 'href' not in params or not params['href']:
        #     links = self.links(int(params['id']), isdump=True)
        #     self.logd('play links', links)
        #     for h in links:
        #         if h['title'] == self.get_setting('play_engine').decode('utf-8'):
        #             params['href'] = h['href']
        #             break
        #     if 'href' not in params or not params['href']:
        #         msg = _('Resource Unavailable or Invalid!')
        #         self.logd('play', msg)
        #         xbmcgui.Dialog().notification(self.name, msg, self.icon, 500)
        #         return None

        href = params['href']
        url = urlparse(href)
        if url.scheme == 'acestream':
            progress = xbmcgui.DialogProgressBG()
            path = self.get_path_acestream(href)
            if not path:
                return None
            try:
                if urlparse(path).port == 6878:

                    progress.create('Ace Stream Engine', self.name)

                    self.log('start acestream play')

                    as_url = 'http://' + '127.0.0.1' + ':' + '6878' + '/ace/getstream?id=' + \
                             urlparse(href).netloc + '&format=json'  # &_idx=" + str(ep)

                    json = eval(self.http_get(as_url).replace(b'null', b'"null"'))["response"]
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
                        j = eval(self.http_get(stat_url).replace(b'null', b'"null"'))["response"]
                        if j == {}:
                            progress.update(i * 3, message=_('wait...'))
                        else:

                            status = j['status']
                            if status == 'dl':
                                progress.update(
                                    i * 3, message=_('playback...'))
                                xbmc.sleep(1000)
                                break
                            progress.update(i * 3, message=_('prebuffering...'))
                            self.logd('get stat acestream - ', j)
                            msg = 'seeds - %s speed - %s download - %s' % (
                                str(j['peers']), str(j['speed_down']), str(int(j['downloaded'] / 1024)))
                            progress.update(i * 3, msg)

                    if i == 29:
                        xbmcgui.Dialog().notification(
                            self.name, _('Torrent not available or invalid!'), self.icon, 500)
                        self.http_get(stop_url)

                    progress.close()
                    xbmc.sleep(1000)
                    path = purl
            except Exception as e:
                xbmcgui.Dialog().notification(
                    self.name, _('Torrent not available or invalid!'), self.icon, 500)
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
            msg = _('Resource Unavailable or Invalid!')
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
        fs = os.listdir(self.profile_dir)
        for f in fs:
            if f != 'settings.xml' and f != 'thumb' and f != '__gettext__.pcl':
                f = os.path.join(self.profile_dir, f)
                os.remove(f)
        self._load_leagues()

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
                    'Select a playback method Ace Straem', list=list)
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
            self.name, _('Changing settings ...'), self.icon, 1000)  # 'Changing settings ...'
        self.update()
        self.settings_changed = False
        xbmc.executebuiltin('Container.Refresh()')

    def reset(self):
        """
        Обновление с удалением файлов данных
        :return:
        """
        xbmcgui.Dialog().notification(self.name, _('Plugin reset...'), self.icon, 500)
        self.log('START RESET DATA')
        self.remove_all()
        self.update()
        self.log('END RESET DATA')
        xbmc.executebuiltin('Dialog.Close(all,true)')
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

    def create_listing_categories(self):
        self.update()
        listing = [
            # {'label': '[UPPERCASE][B][COLOR FF0084FF][{}][/COLOR][/B][/UPPERCASE]'.format(_('League Choice')), 'url': self.get_url(action='select_matches')},
            {'label': '[UPPERCASE][COLOR FFFF0000][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Live')),
             'icon': os.path.join(self.dir('media'), 'live.png'),
             'fanart': self.fanart,
             'url': self.get_url(action='listing', sort='live')},
            {'label': '[UPPERCASE][COLOR FF999999][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Offline')),
             'icon': os.path.join(self.dir('media'), 'offline.png'),
             'fanart': self.fanart,
             'url': self.get_url(action='listing', sort='offline')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('All')),
             'icon': self.icon,
             'fanart': self.fanart,
             'url': self.get_url(action='listing', sort='all')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Football')),
             'icon': os.path.join(self.dir('media'), 'football.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_football.jpg'),
             'url': self.get_url(action='listing', sort='football')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Ice Hockey')),
             'icon': os.path.join(self.dir('media'), 'hockey.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_hockey.jpg'),
             'url': self.get_url(action='listing', sort='hockey')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Basketball')),
             'icon': os.path.join(self.dir('media'), 'basketball.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_basketball.jpg'),
             'url': self.get_url(action='listing', sort='basketball')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Tennis')),
             'icon': os.path.join(self.dir('media'), 'tennis.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_tennis.jpg'),
             'url': self.get_url(action='listing', sort='tennis')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('American Football')),
             'icon': os.path.join(self.dir('media'), 'american_football.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_american_football.jpg'),
             'url': self.get_url(action='listing', sort='american_football')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Race')),
             'icon': os.path.join(self.dir('media'), 'race.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_race.jpg'),
             'url': self.get_url(action='listing', sort='race')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Boxing')),
             'icon': os.path.join(self.dir('media'), 'boxing.png'),
             'fanart': os.path.join(self.dir('media'), 'fanart_boxing.jpg'),
             'url': self.get_url(action='listing', sort='boxing')},
        ]
        return listing
        # return self.create_listing(listing,
        #                     content='movies',
        #                        view_mode=55,
        #                     #    sort_methods=(
        #                     #        xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING),
        #                     cache_to_disk=False)

    def _load_leagues(self):
        file_pickle = os.path.join(self.profile_dir, 'leagues.pickle')
        if os.path.exists(file_pickle):
            with open(file_pickle, 'r') as f:
                return pickle.load(f)
        else:
            data = [_('All'), ]
            with open(file_pickle, 'wt') as f:
                f.write(pickle.dumps(data, 0))
            with open(file_pickle, 'r') as f:
                self.set_setting('selected_leagues', '0')
                return pickle.load(f)

    def _get_selected_leagues(self):
        sl = str(self.get_setting('selected_leagues'))
        if not sl:
            sl = '0'
        return [int(x) for x in sl.split(',')]

    def select_matches(self, params):

        selected_leagues = self._get_selected_leagues()

        result = xbmcgui.Dialog().multiselect(
            _('Choosing a Sports Tournament'), self._load_leagues(), preselect=selected_leagues)

        if result is not None:
            if not len(result):
                result.append(0)
            self.set_setting('selected_leagues', ','.join(str(x)
                                                          for x in result))
            self.on_settings_changed()

    def _parse_listing(self, html, progress=None):
        """
        Парсим страницу для основного списка
        :param html:
        :return: listing = {
                        id : {
                            id: int,
                            label: '',
                            league: '',
                            date: datetime,     должно быть осведомленное время в UTC
                            status: '',
                            thumb: '',
                            icon: '',
                            poster: '',
                            fanart: '',
                            icon1: '',
                            command1: '',
                            icon2: '',
                            command2: '',
                            url_links: '',
                            href: [
                                    {
                                    'href': '',
                                }
                            ]
                        }
                    }
        """
        leagues = self._load_leagues()
        selected_leagues = self._get_selected_leagues()

        listing = {}

        soup = bs4.BeautifulSoup(html, 'html.parser')

        tag_matchs = soup.findAll(
            'li', {'itemtype': 'http://data-vocabulary.org/Event'})

        total = len(tag_matchs)
        still = total
        fill = 0

        for tag_match in tag_matchs:

            # date_away = tag_match.find('meta')['content']
            tag_a = tag_match.find('a')
            game = tag_a['title']
            id_ = int(tag_a['href'].split('/')[-1].split('-')[0])

            icon_sport = tag_a.find('span', {'class': 'sport'}).find('img')[
                'data-src']

            league = tag_a.find('span', {'class': 'competition'}).text

            if league not in leagues:
                leagues.append(league)
                index = leagues.index(league)
                with open(os.path.join(self.profile_dir, 'leagues.pickle'), 'wt') as f:
                    f.write(pickle.dumps(leagues, 0))
                sl = self._get_selected_leagues()
                sl.append(index)
                self.set_setting('selected_leagues',
                                 ','.join(str(x) for x in sl))
            else:
                if not selected_leagues or not selected_leagues[0]:
                    self.log('no filter sports tournament')
                else:
                    if not leagues.index(league) in selected_leagues:
                        still = still - 1
                        continue

            sport = os.path.basename(urlparse(icon_sport).path).split('.')[0]

            icon_sport = os.path.join(self.dir('media'), '{}.png'.format(sport))

            tag_i = tag_a.find('span', {'class': 'date'}).find('i')
            id_event = int(tag_i['id'].split('-')[1])

            if self._language != 'Russian':
                url_links = '{}/engine/modules/sports/sport_refresh.php?' \
                            'from=event&event_id={}&tab_id=undefined&post_id={}&lang=en'.format(
                    self.get_setting('url_site'), id_event, str(id_))
            else:
                url_links = '{}/engine/modules/sports/sport_refresh.php?' \
                            'from=event&event_id={}&tab_id=undefined&post_id={}'.format(
                    self._site, id_event, str(id_))

            # self.logd('url_links', url_links)

            date_naive = tag_i['data-datetime']
            try:
                dt = dateutil.parser.parse(date_naive)
            except ValueError as e:
                if e.message == 'hour must be in 0..23':
                    dt = dateutil.parser.parse(date_naive.split()[0])

            date_utc = self._time_naive_site_to_utc_aware(dt)

            tags_div = tag_a.find(
                'div', {'class': 'commands commands_match_center'}).findAll('div')

            icon1 = tags_div[1].contents[1]['data-src'].replace('?18x18=1', '')
            command1 = tags_div[0].text
            icon2 = tags_div[1].contents[3]['data-src'].replace('?18x18=1', '')
            command2 = tags_div[2].text

            icon = icon_sport
            poster = ''
            thumb = ''
            fanart = os.path.join(self.dir('media'), 'fanart_{}.jpg'.format(sport))

            if self.is_create_artwork():
                art = makeart.ArtWorkFootBall(self,
                                              id=id_,
                                              date=self.time_to_local(date_utc),
                                              league=league,
                                              home=command1,
                                              away=command2,
                                              logo_home=icon1,
                                              logo_away=icon2)

                theme_artwork = self.get_setting('theme_artwork')

                self.log(theme_artwork)

                art.language = self._language

                # Light|Dark|Blue|Transparent

                if theme_artwork == 0:      # Light
                    art.set_light_theme()
                elif theme_artwork == 1:    # Dark
                    art.set_dark_theme()
                elif theme_artwork == 2:    # Blue
                    art.set_blue_theme()
                elif theme_artwork == 3:    # Transparent
                    art.set_transparent_theme()
                else:
                    self.logd('_parse_listing', 'error set artwork theme')
                    art.set_light_theme()

                if self.get_setting('is_thumb'):
                    thumb = art.create_thumb()
                    self.logd('_parse_listing', thumb)
                if self.get_setting('is_fanart'):
                    fanart = art.create_fanart(background=fanart)
                    self.logd('_parse_listing', fanart)
                if self.get_setting('is_poster'):
                    poster = art.create_poster()
                    self.logd('_parse_listing', poster)

            if thumb:
                icon = thumb
            else:
                thumb = icon

            # import web_pdb
            # web_pdb.set_trace()

            listing[id_] = {}
            item = listing[id_]
            item['id'] = id_
            item['id_event'] = id_event
            item['sport'] = sport
            item['status'] = tag_i.text
            item['label'] = game
            item['league'] = league
            item['date'] = date_utc
            item['thumb'] = thumb
            item['icon'] = icon
            item['poster'] = poster
            item['fanart'] = fanart
            item['icon1'] = icon1
            item['command1'] = command1
            item['icon2'] = icon2
            item['command2'] = command2

            item['url_links'] = url_links
            if 'href' is not item:
                item['href'] = []

            self.log('ADD MATCH - %s' % item)

            if progress:
                still = still - 1
                fill = 100 - int(100 * float(still) / total)
                progress.update(fill, message=game)

        return listing

    @staticmethod
    def format_str_column_width(txt, column_width):
        txt = txt.strip()
        result = u'{1:<{0:}}'.format(
            column_width, txt[:column_width] if len(txt) > column_width else txt)
        # print result.encode('utf-8')
        return result

    def _resolve_flash_href(self, href):
        html = self.http_get(href)
        soup = bs4.BeautifulSoup(html, 'html.parser')
        tag_iframe = soup.find('iframe')
        src_html = self.http_get(tag_iframe['src'])
        if src_html is None:
            return ''
        ilink = src_html.find(b'var videoLink')
        if ilink != -1:
            i1 = src_html.find(b'\'', ilink)
            i2 = src_html.find(b'\'', i1 + 1)
            return src_html[i1 + 1:i2]
        else:
            return ''

    def _parse_links(self, id_, html):
        """
        Парсим страницу для списка ссылок
        :param html:
        :return:
        """

        def td_class_text(tr, ntag):
            try:
                return tr.find('td', {'class': ntag}).text
            except:
                return ''

        links = []

        data = json.loads(html)

        broadcast = data.get('broadcast', None)

        if broadcast is not None:
            links.append({
                'label': u'[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('BROADCASTS:')),
                'status': 'title'
            })
            tag_broadcast = bs4.BeautifulSoup(broadcast, 'html.parser')

            tag_li = tag_broadcast.findAll('li')

            for i, li in enumerate(tag_li):

                trs = li.find('table').find('tbody').findAll('tr')

                for tr in trs:

                    tag_img = tr.find('img')
                    if i == 0 and self.get_setting('is_http_link'):
                        href = self._resolve_flash_href(tr.find('a')['href'])
                        if href:
                            links.append(
                                {
                                    'status': 'broadcast',
                                    'icon': tag_img['src'],
                                    'lang': tag_img['title'],
                                    'speed': '',
                                    'channel': '',
                                    'fps': '',
                                    'format': '',
                                    'href': href,
                                }
                            )
                    else:
                        links.append(
                            {
                                'status': 'broadcast',
                                'icon': tag_img['src'],
                                'lang': tag_img['title'],
                                'speed': td_class_text(tr, 'speed'),
                                'channel': td_class_text(tr, 'channel'),
                                'fps': td_class_text(tr, 'fps'),
                                'format': td_class_text(tr, 'format'),
                                'href': tr.find('a')['href'],
                            }
                        )
        reviews = data.get('reviews', None)
        if reviews is not None:
            links.append({
                'label': u'[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('REVIEWS:')),
                'status': 'title'
            })

            home = self.get(id_, 'command1')
            guest = self.get(id_, 'command2')
            lh = len(home)
            lg = len(guest)
            column_width_home = lh if lh >= lg else 2 * lg - lh
            column_width_guest = lg if lg >= lh else 2 * lh - lg

            tag_reviews = bs4.BeautifulSoup(reviews, 'html.parser')
            for li in tag_reviews.findAll('li'):
                class_ = li['class'][0]
                # print class_
                if class_ == u'supermain':
                    links.append({'label': li.text, 'status': 'info'})
                else:
                    if class_ == 'match_review_left':
                        link = self.format_str_column_width(
                            home, column_width_home)
                    else:
                        link = self.format_str_column_width(
                            guest, column_width_guest)
                    div = li.find('div')
                    spans = div.findAll('span')
                    up_down = u''
                    name = u''
                    number = u''
                    icon = u''
                    for s in spans:
                        # print s['class']
                        if len(s['class']) == 2:
                            if s['class'][0] == u'icon':
                                if s['class'][1] == u'block-time':
                                    icon = u'[COLOR FFFFFF00][B][ {} ][/B][/COLOR]'.format(
                                        s.text)
                                elif s['class'][1].find('ball') != -1 or s['class'][1] == 'goal':
                                    icon = u'[COLOR FFFF0000][B]{}[/B][/COLOR]'.format(
                                        _('GOAL'))
                                elif s['class'][1] == 'autogoal':
                                    icon = u'[COLOR FFFF0000][B]{}[/B][/COLOR]'.format(_('AUTOGOAL'))
                                elif s['class'][1] == u'y-card':
                                    icon = u'[COLOR FFFFFF00][{}][/COLOR]'.format(
                                        _('card'))
                                elif s['class'][1] == u'r-card':
                                    icon = u'[COLOR FFFF0000][{}][/COLOR]'.format(
                                        _('card'))
                                elif s['class'][1] == u'up':
                                    up_down = name + \
                                              u'[COLOR FF008000] - {}  [/COLOR]'.format(
                                                  _('came'))
                                    name = u''
                                elif s['class'][1] == u'down':
                                    icon = up_down + name + \
                                           u'[COLOR FFFF0000] - {}[/COLOR]'.format(
                                               _('gone'))
                                    up_down = u''
                                    name = u''
                        else:
                            if s['class'][0] == u'name':
                                name = s.text
                            elif s['class'][0] == u'number':
                                number = s.text
                    link = link + u'    ' + number + u'   ' + icon + u'   ' + name
                    links.append({'label': link, 'status': 'info'})
        eventsstat = data.get('eventsstat', None)
        if eventsstat is not None:
            links.append({
                'label': u'[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('STATISTICS:')),
                'status': 'title'
            })
            content = eventsstat[0].get('content', None)
            if content is not None:
                tag_content = bs4.BeautifulSoup(content, 'html.parser')
                if tag_content:
                    for tabl in tag_content.findAll('table'):
                        tags_td = tabl.findAll('td')
                        links.append({
                            'label': u'{}  -   {}   -  {}'.format(tags_td[0].text,
                                                                  tags_td[2].text,
                                                                  tags_td[4].text),
                            'status': 'info'
                        })

        return links

    def _get_links(self, id_, links):
        """
        Возвращаем список ссылок для папки конкретного элемента
        :param id:
        :return:
        """

        title = self.get(id_, 'label')
        info_mini = self._get_mini_info_math(self.get(id_, 'id_event'))
        plot = u'%s\n%s\n%s\n\n[B]                  %s  :  %s[/B]' % (
            self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
            self.get(
                id_, 'league'),
            self.get(
                id_, 'label'),
            info_mini['scorel'],
            info_mini['scorer']
        )

        l = []

        l.append({'label': u'{}       {}'.format(self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
                                                 self.get(id_, 'league')),
                  'info': {'video': {'title': title, 'plot': plot}},
                  'icon': self.get(id_, 'icon'),
                  'fanart': self.get(id_, 'fanart'),
                  'url': '',
                  'is_playable': False,
                  'is_folder': False})

        l.append({'label': u'[B]{}    {} : {}    {} [/B]'.format(self.get(id_, 'command1'), info_mini['scorel'],
                                                                 info_mini['scorer'], self.get(id_, 'command2')),
                  'info': {'video': {'title': title, 'plot': plot}},
                  'icon': self.get(id_, 'icon'),
                  'fanart': self.get(id_, 'fanart'),
                  'url': '',
                  'is_playable': False,
                  'is_folder': False})

        for link in links:
            if link['status'] == 'broadcast':
                label = ''
                urlprs = urlparse(link['href'])

                if urlprs.scheme == 'acestream':
                    icon = os.path.join(self.dir('media'), 'ace.png')
                    label = '[COLOR FF00A550][AceStream][/COLOR]'
                    label = '{} | {} | {} | {} - ({})'.format(
                        label, link['speed'], link['channel'], link['format'], link['lang'])
                elif urlprs.scheme == 'sop':
                    icon = os.path.join(self.dir('media'), 'sop.png')
                    label = '[COLOR FF42AAFF][ SopCast ][/COLOR]'
                    label = '{} | {} | {} | {} - ({})'.format(
                        label, link['speed'], link['channel'], link['format'], link['lang'])
                    # plot = plot + u'\n\n' + _('Plexus plugin required to view SopCast').decode('utf-8')
                else:
                    if self.get_setting('is_http_link'):
                        label = '[COLOR FFFFFFFF][  http  ] - {}[/COLOR]'.format(_('direct link to broadcast'))
                        label = '{} - ({})'.format(label, link['lang'])
                        icon = os.path.join(self.dir('media'), 'http.png')
                        self.logd('_get_links https', link['href'])

                if label:
                    l.append({'label': label,
                              'info': {'video': {'title': title, 'plot': plot}},
                              'thumb': icon,
                              'icon': icon,
                              'fanart': self.get(id_, 'fanart'),
                              'art': {'icon': icon, 'thumb': icon, },
                              'url': self.get_url(action='play', href=link['href'], id=id_),
                              'is_playable': True})
            else:
                l.append({'label': link['label'],
                          'info': {'video': {'title': title, 'plot': plot}},
                          'icon': self.get(id_, 'icon'),
                          'fanart': self.get(id_, 'fanart'),
                          'url': '',
                          'is_playable': False,
                          'is_folder': False})

        if len(l) == 3:
            l.append({'label': _('Stream information will be available 30 minutes prior to the begining of an event.'),
                      'info': {'video': {'title': self._site, 'plot': self._site}},
                      'icon': self.icon,
                      'url': self.get_url(action='play', href=URL_NOT_LINKS),
                      'is_playable': True})

        return l

    def _get_match_center_mini(self):
        center = self.http_get(
            'https://moon.livesport.ws/engine/modules/sports/sport_template_loader.php?'
            'from=showfull&template=match/main_match_center_mini_refresher')

        center = center.decode('unicode-escape')
        center = center[center.find('{'):]

        if center:
            center = json.loads(center)
        else:
            return None
        return center

    def _get_mini_info_math(self, id_event, center=None):
        if center is not None:
            for info in center['match_center_mini']:
                if info['event'] == str(id_event):
                    return info
        else:
            center = self._get_match_center_mini()
            return self._get_mini_info_math(id_event, center)
        return None

    def create_listing_filter(self, params):
        l = []
        if params['sort'] != 'offline':
            l.append({'label': '[UPPERCASE][B][COLOR FF0084FF][{}][/COLOR][/UPPERCASE][/B]'.format(_('Refresh')),
                      'url': self.get_url(action='listing', sort=params['sort']),
                      'icon': os.path.join(self.dir('media'), 'refresh.png')})
        # return l + self._get_listing(params=params)
        return self.create_listing(l + self._get_listing(params=params),
                                   content='movies',
                                   #    view_mode=55,
                                   #    sort_methods=(
                                   #        xbmcplugin.SORT_METHOD_DATEADDED, xbmcplugin.SORT_METHOD_VIDEO_RATING),
                                   cache_to_disk=False)

    def format_timedelta(self, dt, pref):
        if self._language == 'Russian':
            h = int(dt.seconds / 3600)
            return '{} {} {} {:02} мин.'.format(pref, '%s дн.' % dt.days if dt.days else '',
                                                '%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))
        else:
            return '{} {}'.format(pref, str(dt).split('.')[0])

    def _get_listing(self, params=None):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        # import web_pdb
        # web_pdb.set_trace()

        filter_ = params['sort']

        listing = []

        now_utc = self.time_now_utc()

        self.logd('_get_listing()', '%s' % self.time_to_local(now_utc))

        center = self._get_match_center_mini()

        try:
            for item in list(self._listing.values()):

                info_match = self._get_mini_info_math(item['id_event'], center)

                if not info_match:
                    self.logd('_get_listing() - not info_match', item['label'])
                    continue

                # self.logd(filter, info_match['status'])

                if not (filter_ is None or filter_ == 'all' or filter_ == 'live' or filter_ == 'offline'):
                    if filter_ != item['sport']:
                        continue

                if self.get_setting('is_noold_item') and info_match['status'] == u'OFFLINE' and filter_ != 'offline':
                    continue

                if filter_ == 'live' and info_match['status'] != u'LIVE':
                    continue

                if filter_ == 'offline' and info_match['status'] != u'OFFLINE':
                    continue

                status = 'FFFFFFFF'

                # import web_pdb
                # web_pdb.set_trace()

                date_ = item['date']
                if info_match['status'] == 'OFFLINE':
                    dt = now_utc - date_
                    plot = self.format_timedelta(dt, _('Offline'))
                elif info_match['status'] == 'LIVE':
                    dt = now_utc - date_
                    plot = u'%s %s мин.' % (_('Live'), int(dt.total_seconds() / 60))
                else:
                    dt = date_ - now_utc
                    plot = self.format_timedelta(dt, _('After'))

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, self.time_to_local(date_).strftime('%d.%m %H:%M'), item['label'], item['league'])

                if info_match is not None and (info_match['status'] == u'OFFLINE' or info_match['status'] == u'LIVE'):
                    lab = u'[B]{} - {}[/B]  {}'.format(
                        info_match['scorel'], info_match['scorer'], info_match['status'])
                    if info_match['status'] == 'OFFLINE':
                        status = 'FF999999'
                    elif info_match['status'] == 'LIVE':
                        status = 'FFFF0000'
                else:
                    lab = self.time_to_local(date_).strftime(
                        '%d.%m %H:%M' if self.get_setting('is_date_item') else '%H:%M')

                label = '[COLOR %s]%s[/COLOR] - [B]%s[/B]    %s' % (status, lab, item['label'],
                                                                     item['league'] if self.get_setting(
                                                                         'is_league_item') else '')

                plot = title + '\n' + plot + '\n\n' + self._site

                href = ''

                if self.get_setting('is_play'):
                    for h in item['href']:
                        if h['title'] == self.get_setting('play_engine'):
                            href = h['href']
                            break

                is_folder, is_playable, get_url = self.geturl_isfolder_isplay(item['id'], href)

                listing.append({
                    'label': label,
                    'art': {
                        'thumb': item['thumb'],
                        'poster': item['poster'],
                        'fanart': item['fanart'],
                        'icon': item['thumb'],
                    },
                    'info': {
                        'video': {
                            # 'year': '',
                            'plot': plot,
                            'title': label,
                        }
                    },
                    # 'offscreen': False,
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': get_url,
                })

        except Exception as e:
            self.logd('._get_listing() ERROR', str(e))

        return listing


plugin = LiveSport()
_ = plugin.initialize_gettext()

