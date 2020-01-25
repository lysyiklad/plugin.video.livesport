# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from future import standard_library

standard_library.install_aliases()
import requests
import urllib
import pickle
import re
from . import simpleplugin
import xbmcgui
import xbmc
# import xbmcplugin
from dateutil.tz import tzutc, tzlocal, tzoffset
from dateutil.parser import *
import dateutil
import bs4
from urllib.parse import urlparse
from collections import OrderedDict
import os
import json
import datetime
from builtins import range
from builtins import str

# URL_NOT_LINKS = 'https://www.ixbt.com/multimedia/video-methodology/bitrates/avc-1080-25p/1080-25p-10mbps.mp4'
URL_NOT_LINKS = 'http://tv-na-stene.ru/files/HD%20Red.mkv'

USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0(compatible; MSIE 6.0; ' \
             'Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; ' \
             '.NET CLR 3.5.30729; .NET4.0C)'

HEADERS_HTTP = {'User-Agent': USER_AGENT}


def file_read(file):
    with open(file, 'rt') as f:  # , encoding="utf-8" , errors='ignore'
        try:
            return f.read()
        except Exception as e:
            print(e)
    return ''


class PluginSport(simpleplugin.Plugin):

    def __init__(self):
        super(PluginSport, self).__init__()
        global _
        self._dir = {'media': os.path.join(self.path, 'resources', 'media'),
                     'data': os.path.join(self.path, 'resources', 'data'),
                     'font': os.path.join(self.path, 'resources', 'data', 'font'),
                     'lib': os.path.join(self.path, 'resources', 'lib'),
                     'thumb': os.path.join(self.profile_dir, 'thumb')}

        if not os.path.exists(self.dir('thumb')):
            os.mkdir(self.dir('thumb'))

        self._site = self.get_setting('url_site')
        self.settings_changed = False
        self.stop_update = False

        self._date_scan = None  # Время сканирования в utc
        self._listing = OrderedDict()

        self._language = xbmc.getInfoLabel('System.Language')  # Russian English

        if self._language != 'Russian':
            self._site = os.path.join(self.get_setting('url_site'), 'en')
        else:
            self._site = self.get_setting('url_site')

        self._progress = xbmcgui.DialogProgressBG()

        self._leagues = OrderedDict()
        self._leagues_artwork = OrderedDict()

        self._icons_league_pcl = os.path.join(self.profile_dir, 'iconleague.pcl')

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
    def format_str_column_width(txt, column_width):
        txt = txt.strip()
        result = u'{1:<{0:}}'.format(
            column_width, txt[:column_width] if len(txt) > column_width else txt)
        return result

    @property
    def date_scan(self):
        return self._date_scan

    @property
    def version_kodi(self):
        return int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def dir(self, dir_):
        return self._dir[dir_]

    def get_item(self, id_):
        item = self._listing.get(id_, None)
        if item is None:
            self.update()
            item = self._listing.get(id_, None)
            if item is None:
                return None
        return item

    def get(self, id_, key):
        return self.get_item(id_).get(key, None)

    def load(self):
        try:
            with self.get_storage() as storage:
                self._listing = storage['listing']
                self._date_scan = storage['date_scan']
                self._leagues = storage['leagues']
                self._leagues_artwork = storage['leagues_artwork']
        except Exception as e:
            self.logd('ERROR load data', e)

    def dump(self):
        try:
            with self.get_storage() as storage:
                storage['listing'] = self._listing
                storage['date_scan'] = self._date_scan
                storage['leagues'] = self._leagues
                storage['leagues_artwork'] = self._leagues_artwork
        except Exception as e:
            self.logd('ERROR dump data', e)

    def _selected_leagues(self, leagues, title):

        selected_old = self._get_selected_leagues(leagues)
        if self.version_kodi < 17:
            selected = xbmcgui.Dialog().multiselect(title, leagues.keys())
        else:
            selected = xbmcgui.Dialog().multiselect(title, leagues.keys(), preselect=selected_old, useDetails=False)
        if selected is not None and selected != selected_old:
            self._set_selected_leagues(selected, leagues)
            self.logd('selected_leagues', selected)
            self.dump()
            #  with self.get_storage() as storage:
            #      storage['leagues'] = self._leagues

            self.on_settings_changed()

    def _get_selected_leagues(self, leagues):
        return [index for index, item in enumerate(leagues.items()) if item[1]]

    def _set_selected_leagues(self, selected, leagues):
        for index, item in enumerate(leagues.items()):
            leagues[item[0]] = False
            if index in selected:
                leagues[item[0]] = True

    def _add_league(self, league):
        if self._leagues.get(league, None) is None:
            self._leagues[league] = True
            self._leagues_artwork[league] = True
            self.dump()
        #  with self.get_storage() as storage:
        #      storage['leagues'] = self._leagues

    def selected_leagues(self):
        self._selected_leagues(self._leagues, _('Choosing a Sports Tournament'))

    def _is_league(self, league, leagues):
        if leagues.get(league, None) is not None:
            if not leagues[league]:
                return False
        else:
            self._add_league(league)
        return True

    def selected_leagues_artwork(self):
        self._selected_leagues(self._leagues_artwork, _('Select leagues to create ArtWork...'))

    def get_http(self, url):
        try:
            self.log('HTTP GET - URL {}'.format(url))
            r = requests.get(url, headers=HEADERS_HTTP, timeout=10)
            self.log(r.status_code)
            for it in r.headers.items():
                self.log('{}: {}'.format(it[0], it[1]))
            return r
        except requests.exceptions.ReadTimeout:
            err = 'HTTP ERROR: Read timeout occured'
        except requests.exceptions.ConnectTimeout:
            err = 'HTTP ERROR: Connection timeout occured!'
        except requests.exceptions.ConnectionError:
            err = 'HTTP ERROR: Seems like dns lookup failed..'
        except requests.exceptions.HTTPError as err:
            err = 'HTTP ERROR: HTTP Error occured'
            err += 'Response is: {content}'.format(content=err.response.content)

        self.log(err)
        raise Exception(err)

    #       return ''

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
        id_ = int(params.id)
        links = self.links(id_, isdump=False)
        self.logd('links', links)

        return self._get_links(id_, links)

    def links(self, id_, isdump=False):
        """
        Возвращает список ссылок кокретного элемента. При необходимости парсит по ссылке в элементе.
        :param id_: id элемента
        :return:
        """
        links = self.get(id_, 'href')
        item = self.get_item(id_)
        self.logd('links', 'item %s' % item)
        self.logd('links', 'date_links %s' % item['date_links'])
        scan_now = None
        # if links:
        #     scan_now = int((self.time_now_utc() - item['date_links']).total_seconds() / 60)

        self.logd('links', 'id %s' % id_)
        self.logd('links', links)
        self.logd('links', 'scan_now %s' % scan_now)

        if scan_now is None or self.get_setting('delta_links') < scan_now:

            try:
                html = self.get_http(self.get(id_, 'url_links')).content
            except Exception as e:
                xbmcgui.Dialog().notification(self.name, str(e), self.icon, 2000)
                self.logd('ERROR LINKS', str(e))
            finally:
                if not html:
                    self.logd('links', 'not html')
                    return links
            del links[:]
            links.extend(self._parse_links(id_, html))

            if links:
                item['date_links'] = self.time_now_utc()
            else:
                item['date_links'] = None
            self.logd('links', 'date_links %s' % item['date_links'])
            # if isdump and links and status == 'OFFLINE':
            #     # self.dump()
            #     with self.get_storage() as storage:
            #         storage['listing'] = self._listing

        self.logd('self.get(%s, href)' % id_, self.get(id_, 'href'))

        return links

    def update(self):
        """
        Обновление списков для виртуальных папок, рисунков, удаление мусора, сохранение в pickle
        :return:
        """

        self.load()

        self.logd('plugin.update - self.settings_changed', self.settings_changed)

        for it in self._leagues.items():
            self.log('update self._leagues - {}: {}'.format(it[0], it[1]))

        if not self.is_update():
            return

        # progress = xbmcgui.DialogProgressBG()

        self._progress.create(self.name, _('UPDATE DATA ...'))

        try:

            self.log('START UPDATE')

            self._progress.update(1, message=_('Loading site data ...'))

            # import web_pdb
            # web_pdb.set_trace()

            html = self.get_http(self._site).content

            # self.log(html)

            # file_html = os.path.join(self.path, 'listing.html')
            # if not os.path.exists(file_html):
            #     with open(file_html, 'wb') as f:
            #         f.write(html)

            # html = file_read(file_html)

            self.log('***** 1')
            self._listing = self._parse_listing(html, progress=self._progress)
            self.log('***** 2')

            if not self._listing:
                try:
                    if self._progress:
                        self._progress.close()
                except:
                    pass
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

            self.log('***** 4')

            self._listing = OrderedDict(sorted(list(self._listing.items()), key=lambda t: t[1]['date']))
            self.log('***** 5')
            self._date_scan = self.time_now_utc()
            self.dump()
            self.log(
                'STOP UPDATE [date scan = {} - _time_scan_now() = {}]'.format(self.date_scan, self._time_scan_now()))
            self._progress.update(100, self.name, _('End update...'))


        except Exception as e:
            xbmcgui.Dialog().notification(self.name, str(e), xbmcgui.NOTIFICATION_ERROR, 10000)
            self.logd('ERROR UPDATE', str(e))
        finally:
            xbmc.sleep(500)
            self.log('***** 6')
            try:
                if self._progress:
                    self._progress.close()
            except:
                pass

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
            if not os.path.exists(os.path.join(self.profile_dir, 'storage.pcl')):
                self.logd('is_update', 'True - not os.path.exists(storage.pcl)')
                return True
            if not self._listing:
                self.logd('is_update', 'True - not self._listing')
                return True
            if self._time_scan_now() > self.get_setting('delta_scan'):
                self.logd(
                    'is_update',
                    'True - self._time_scan_now() {} > self.get_setting(delta_scan) {}'.format(self._time_scan_now(),
                                                                                               self.get_setting(
                                                                                                   'delta_scan')))
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

        href = params.href
        url = urlparse(href)
        if url.scheme == 'acestream':
            progress = xbmcgui.DialogProgressBG()
            path = self.get_path_acestream(href)
            if not path:
                return None
            try:

                if urlparse(path).port == 6878:

                    progress.create('Ace Stream Engine', self.name)

                    self.log('start acestream play - host - {} - port {}'.format(urlparse(path).hostname,
                                                                                 urlparse(path).port))

                    as_url = 'http://' + urlparse(path).hostname + ':' + '6878' + '/ace/getstream?id=' + \
                             urlparse(href).netloc + '&format=json'  # &_idx=" + str(ep)

                    json_response = requests.get(as_url).json()["response"]
                    self.log(json_response)
                    stat_url = json_response["stat_url"]
                    self.logd('stat_url', stat_url)
                    stop_url = json_response["command_url"] + '?method=stop'
                    self.logd('stop_url', stop_url)
                    purl = json_response["playback_url"]
                    self.logd('purl', purl)

                    for i in range(30):
                        xbmc.sleep(1000)
                        j = requests.get(stat_url).json()["response"]
                        if j == {}:
                            progress.update(i * 3, message=_('wait...'))
                        else:

                            status = j['status']
                            if status == 'dl':
                                progress.update(i * 3, message=_('playback...'))
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
                        requests.get(stop_url)

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
        elif url.netloc == 'stream.livesport.ws':
            path = self._resolve_direct_link(url.geturl())
        else:
            path = url.geturl()

        if not path:
            msg = _('Resource Unavailable or Invalid!')
            xbmcgui.Dialog().notification(self.name, msg, self.icon, 500)
            self.logd('play', msg)
            return None

        self.logd('play', 'PATH PLAY: %s' % path)

        params = {'sender': self.id,
                  'message': 'resolve_url',
                  'data': {'command': 'Play.Live',
                           'id': params.id,
                           },
                  }

        command = json.dumps({'jsonrpc': '2.0',
                              'method': 'JSONRPC.NotifyAll',
                              'params': params,
                              'id': 1,
                              })

        result = xbmc.executeJSONRPC(command)

        self.logd('play', 'result xbmc.executeJSONRPC {}'.format(result))

        # return self.resolve_url(path, succeeded=True)
        return path

    @staticmethod
    def time_now_utc():
        """
        Возвращает текущее осведомленное(aware) время в UTC
        :return:
        """
        return datetime.datetime.now(tz=tzutc())

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
        return dt.astimezone(tzutc())

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

    def _format_timedelta(self, dt, pref):
        if self._language == 'Russian':
            h = int(dt.seconds / 3600)
            return '{} {} {} {:02} мин.'.format(pref, '%s дн.' % dt.days if dt.days else '',
                                                '%s ч.' % h if h else u'', int(dt.seconds % 3600 / 60))
        else:
            return '{} {}'.format(pref, str(dt).split('.')[0])

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

    def clear(self):
        """

        :return: 
        """
        pics = os.listdir(self.dir('thumb'))
        for pic in pics:
            pic = os.path.join(self.dir('thumb'), pic)
            self.remove_thumb(pic)
        fs = os.listdir(self.profile_dir)
        self._date_scan = None
        self._listing.clear()
        self._leagues.clear()
        self._leagues_artwork.clear()
        self.dump()

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
        xbmcgui.Dialog().notification(self.name, _('Changing settings ...'), self.icon, 1000)
        self.update()
        self.settings_changed = False
        xbmc.executebuiltin('Container.Refresh()')

    def reset(self):
        """
        Обновление с удалением файлов данных
        :return:
        """
        xbmcgui.Dialog().notification(self.name, _('Plugin data reset...'), self.icon, 500)
        self.log('START RESET DATA')
        self.clear()
        self.update()
        self.log('END RESET DATA')
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


class LiveSport(PluginSport):

    # import web_pdb
    # web_pdb.set_trace()

    def create_listing_categories(self):
        listing = [
            {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Extra')),
             'icon': os.path.join(self.dir('media'), 'extra.png'), 'fanart': self.fanart,
             'url': self.get_url(action='extra')},
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

    def create_listing_extra(self):
        listing = [
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Leagues Choice...')),
             'icon': os.path.join(self.dir('media'), 'select.png'), 'fanart': self.fanart,
             'url': self.get_url(action='select_leagues')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Select leagues to create ArtWork...')),
             'icon': os.path.join(self.dir('media'), 'selectart.png'), 'fanart': self.fanart,
             'url': self.get_url(action='select_leagues_artwork')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Add-on settings...')),
             'icon': os.path.join(self.dir('media'), 'extra.png'),
             'fanart': self.fanart, 'url': self.get_url(action='settings')},
            {'label': '[UPPERCASE][B]{}[/B][/UPPERCASE]'.format(_('Plugin data reset...')),
             'icon': os.path.join(self.dir('media'), 'reset.png'),
             'fanart': self.fanart, 'url': self.get_url(action='reset')}
        ]
        return listing

    @staticmethod
    def find_src(html, tag, quotes, start=0):
        i1 = html.find(quotes, html.find(tag, start))
        return html[i1 + 1:html.find(quotes, i1 + 1)]

    def _resolve_direct_link(self, href):

        link = ''
        try:
            html = self.get_http(href).content
            self.logd('_resolve_direct_link - href', href)
            soup = bs4.BeautifulSoup(html, 'html.parser')
            tag_iframe = soup.find('iframe')
            src = tag_iframe['src']
            self.logd('_resolve_direct_link - iframe src', src)
            prs = urlparse(src)
            if prs.netloc == '365lives.net':
                src_html = self.get_http('https://api.livesports24.online/gethost').content
                link = 'https://' + src_html + '/' + prs.path.split('/')[-1] + '.m3u8'
            elif prs.netloc == 'whd365.pro':
                link = 'https://185-198-56-58.livesports24.online/{}.m3u8'.format(prs.path.split('/')[-1])
            elif prs.netloc == '777sportba.com' or prs.netloc == 'mmm.08sportbar.com':
                link = self.find_src(self.get_http(src).content, b'var videoLink', b'\'')
                if not urlparse(link).scheme:
                    link = 'https:' + link
                #self.log(self.get_http(src).content)
                # link = link.replace('777sportba.com', 'mmm.08sportbar.com')
            elif prs.netloc == 'sportsbay.org':
                link = src
            elif prs.netloc == 'dummyview.online':
                src_json = 'http://185.255.96.166:3007/api/streams/2/channels/' + prs.path.split('/')[-1]
                self.logd('_resolve_direct_link - src_json', src_json)
                data_json = self.get_http(src_json).json()
                self.logd('_resolve_direct_link - data_json', data_json)
                src = data_json['data']['sourceUrl']
                self.logd('_resolve_direct_link - src', src)
                if urlparse(src).netloc == 'ok.ru':
                    tok = bs4.BeautifulSoup(self.get_http(src).content, 'html.parser')
                    # self.logd('_resolve_direct_link - ok.ru', tok)
                    do = json.loads(tok.find("div", {"data-options": re.compile(r".*")})['data-options'])
                    self.logd('_resolve_direct_link - data_options', do)
                    link = json.loads(do['flashvars']['metadata'])['hlsMasterPlaylistUrl']
                elif urlparse(src).netloc == 'rutube.ru':
                    link = src
                elif urlparse(src).netloc == 'box-live.stream':
                    h = self.get_http(src).content
                    link = self.find_src(h, b'source:', b'\'', h.find(b'new Clappr.Player({'))
                elif urlparse(src).netloc == 'bilasport.net':
                    link = src
            elif prs.netloc == 'flowframes.online':
                link = src
            elif prs.netloc == 'assia.tv':
                link = self.find_src(self.get_http(src).content, b'file:', b'\"')
            elif prs.netloc == 'vamosplay.tech':
                link = 'http://51.91.16.61/channels/{}/stream.m3u8'.format(prs.path.split('/')[-1])

        except Exception as e:
            xbmcgui.Dialog().notification(self.name, str(e), self.icon, 2000)
            self.logd('ERROR RESOLVE HREF ({})'.format(href), str(e))
            return ''
        if link:
            p = urlparse(link)
            xbmcgui.Dialog().notification(self.name, p.scheme + '://' + p.netloc + '/', self.icon, 3000)

        USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3730.0 Safari/537.36'
        # link = '{0}|Referer={1}&User-Agent={2}'.format(link, urllib.quote(link, safe=''), USER_AGENT)
        link = '{0}|User-Agent={1}'.format(link, USER_AGENT)
        self.logd('_resolve_direct_link - link', link)
        return link

    def _get_match_center_mini(self):
        try:
            center = self.get_http('https://moon.livesport.ws/engine/modules/sports/sport_template_loader.php?'
                                   'from=showfull&template=match/main_match_center_mini_refresher').content
        except Exception as e:
            self.logd('ERROR GET MATCH CENTER MINI', str(e))
            return None

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
        if params['sort'] != 'offline' and self.get_setting('is_button_refresh'):
            l.append({'label': '[UPPERCASE][B][COLOR FF0084FF][{}][/COLOR][/UPPERCASE][/B]'.format(_('Refresh')),
                      'url': self.get_url(action='listing', sort=params['sort']),
                      'poster': os.path.join(self.dir('media'), 'refresh.png'),
                      'art': {
                          'thumb': os.path.join(self.dir('media'), 'refresh.png'),
                          'poster': os.path.join(self.dir('media'), 'refresh.png'),
                          'fanart': self.fanart,
                          'icon': os.path.join(self.dir('media'), 'refresh.png'),
                      },
                      'info': {
                          'video': {
                              'plot': _('Updating Lists'),
                          }
                      },
                      })
        # return l + self._get_listing(params=params)
        return self.create_listing(l + self._get_listing(params=params),
                                   content='movies',
                                   cache_to_disk=False)

    def get_labels_live(self):

        if not self.get_setting('is_live_fullscreenvideo'):
            return []

        labels = [u'[UPPERCASE][COLOR FF0084FF][B]{}:[/B][/COLOR][/UPPERCASE]'.format(_('Live'))]

        center = self._get_match_center_mini()

        try:
            for item in list(self._listing.values()):

                info_match = self._get_mini_info_math(item['id_event'], center)

                if not info_match:
                    self.logd('_get_listing() if not info_match', item['label'])
                    continue

                if info_match['status'] != u'LIVE':
                    continue

                if not item['home']:
                    continue

                labels.append(
                    u'[B]{} - {}[/B]  {}'.format(info_match['scorel'], info_match['scorer'], item['label'])
                )

        except Exception as e:
            self.logd('._get_labels_live() ERROR', str(e))

        return labels

    # def get_labels_live(self):
    #
    #     labels = [u'[UPPERCASE][COLOR FF0084FF][B]{}:[/B][/COLOR][/UPPERCASE]'.format(_('Live'))]
    #
    #     try:
    #         for item in list(self._listing.values()):
    #
    #             is_live = False
    #
    #             scorel = ''
    #             scorer = ''
    #
    #             url_links = item.get('url_links', None)
    #             if url_links is not None:
    #                 data = self.get_http(url_links).json()
    #                 if data.get('broadcast_status', None) == 1:
    #                     events = data.get('events', None)
    #                     if events is not None:
    #                         if events[2] != _('Completed'):
    #                             scorel = events[0]
    #                             scorer = events[1]
    #                             is_live = True
    #
    #             if is_live:
    #                 labels.append(u'[B]{} - {}[/B]  {}'.format(scorel, scorer, item['label']))
    #
    #     except Exception as e:
    #         self.logd('._get_labels_live() ERROR', str(e))
    #
    #     return labels

    def get_labels_status_match(self, id_):

        labels = []

        links = self.links(id_)

        # info_mini = self._get_mini_info_math(self.get(id_, 'id_event'))

        labels.append(u'{}       {}'.format(self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
                                            self.get(id_, 'league')))

        # labels.append(u'[B]{}    {} : {}    {} [/B]'.format(self.get(id_, 'home'), info_mini['scorel'],
        #                                                     info_mini['scorer'], self.get(id_, 'guest')))

        data = links[0]['data']

        scorel = '' if data['events'] is None else data['events'][0]
        scorer = '' if data['events'] is None else data['events'][1]

        if self.get(id_, 'home'):
            labels.append(u'[B]{}    {} : {}    {} [/B]'.format(self.get(id_, 'home'), scorel,
                                                                scorer, self.get(id_, 'guest')))

        label_broadcast = '[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('BROADCASTS:'))
        label_reviews = '[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('REVIEWS:'))
        label_statistic = '[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('STATISTICS:'))

        is_reviews = self.get_setting('is_reviews_fullscreenvideo')
        is_statistics = self.get_setting('is_statistic_fullscreenvideo')
        is_append = True

        for link in links:
            if link.get('status', '') != 'broadcast' \
                    and link.get('status', '') != 'data' \
                    and link['label'] != label_broadcast:
                if link['label'] == label_reviews and not is_reviews:
                    is_append = False
                if link['label'] == label_statistic:
                    if not is_statistics:
                        is_append = False
                    else:
                        is_append = True

                if is_append:
                    labels.append(link['label'])

        return labels

    # @staticmethod
    # def remove_square_brackets(txt):
    #     return re.sub('[\[].*?[\]]', '', txt)

    # @staticmethod
    # def format_str_column_width_new(label, column_width):
    #     #txt = txt.strip()
    #     #print('txt - {}'.format(str(txt)))
    #     len_label = len(label)
    #     label_real = LiveSport.remove_square_brackets(label)
    #     len_label_real = len(label_real)
    #
    #     label_utf8 = label.encode('utf-8')
    #     len_label_utf8 = len(label_utf8)
    #     label_real_utf8 = label_real.encode('utf-8')
    #     len_label_real_utf8 = len(label_real_utf8)
    #
    #     #print('len_service - {}'.format(len_service))
    #
    #     # print('real txt - {}'.format(LiveSport.remove_square_brackets(txt)))
    #     # print('len_real - {}'.format(len(LiveSport.remove_square_brackets(txt))))
    #     # print('column_width - {}'.format(column_width))
    #     # print('len_service - len_real - {}'.format(len_service - len_real))
    #     # print('column_width - (len_service - len_real) - {}'.format(column_width - (len_service - len_real)))
    #     #result = '{1:{0:}s}  |'.format(column_width + (len_service - len_real), txt)
    #     result = '{}{}|'.format(label, ' '.join('*' for a in range(column_width - (len_label - len_real))))
    #     return result
    #
    # def create_labels(self, id_):
    #     row = 20
    #     live = self.get_labels_live()
    #     status = self.get_labels_status_match(id_)
    #     # probel = ['', '', '', '']
    #     # status = status + probel
    #     sl = status + live
    #     labels = []
    #     if len(sl) > row:
    #         for i, v in enumerate(sl):
    #             if i == row:
    #                 break
    #             if (i + row) < len(sl):
    #                 labels.append('{}{}'.format(self.format_str_column_width_new(sl[i], 60),  sl[i + row]))
    #             else:
    #                 labels.append('{}'.format(self.format_str_column_width_new(sl[i], 60)))
    #         return labels
    #     return sl

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
                            icon_home: '',
                            home: '',
                            icon_guest: '',
                            guest: '',
                            url_links: '',
                            href: [
                                    {
                                    'href': '',
                                }
                            ]
                        }
                    }
        """
        icons_league = {}

        if os.path.exists(self._icons_league_pcl):
            with open(self._icons_league_pcl, 'rb') as f:
                icons_league = pickle.load(f)

        listing = {}

        soup = bs4.BeautifulSoup(html, 'html.parser')

        tag_matchs = soup.findAll('li', {'itemtype': 'http://data-vocabulary.org/Event'})

        total = len(tag_matchs)
        still = total
        fill = 0

        import_error = False

        for tag_match in tag_matchs:

            try:

                tag_a = tag_match.find('a')
                game = tag_a['title']
                id_ = int(tag_a['href'].split('/')[-1].split('-')[0])

                icon_sport = tag_a.find('span', {'class': 'sport'}).find('img')['data-src']

                #league = tag_a.find('span', {'class': 'competition'}).text
                league = tag_a.findAll('span')[-1].text

                if not self._is_league(league, self._leagues):
                    still = still - 1
                    continue

                icon_league = ''

                if league not in icons_league:
                    try:
                        href = self.get_setting('url_site') + tag_a['href']

                        file_html = os.path.join(self.path, 'links2.html')

                        h = self.get_http(href).content

                        s = bs4.BeautifulSoup(h, 'html.parser')

                        tag_figure = s.find('figure', {'class': 'visual'})
                        tag_image = tag_figure.find('img')
                        icons_league[league] = tag_image['src']
                        icon_league = tag_image['src']

                        with open(self._icons_league_pcl, 'wb') as f:
                            pickle.dump(icons_league, f)

                    except:
                        pass
                else:
                    icon_league = icons_league[league]

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

                date_naive = tag_i['data-datetime']
                # self.logd('date_naive', date_naive)
                try:
                    dt = dateutil.parser.parse(date_naive, dayfirst=True)
                except ValueError as e:
                    self.logd('_parse_listing ERROR DATEUTIL PARSE', str(e))
                    if e.message == 'hour must be in 0..23':
                        dt = dateutil.parser.parse(date_naive.split()[0])

                date_utc = self._time_naive_site_to_utc_aware(dt)

                try:
                    tags_div = tag_a.find('div', {'class': 'commands commands_match_center'}).findAll('div')

                    icon_home = tags_div[1].findAll('img')[0]['data-src'].replace('?18x18=1', '')

                    home = tags_div[0].text
                    icon_guest = tags_div[1].findAll('img')[1]['data-src'].replace('?18x18=1', '')

                    guest = tags_div[2].text
                except:
                    icon_home = ''
                    home = ''
                    icon_guest = ''
                    guest = ''
                    game = ' '


                icon = icon_sport if not icon_league else icon_league
                poster = ''
                thumb = ''
                fanart = os.path.join(self.dir('media'), 'fanart_{}.jpg'.format(sport))

                if not import_error and self.is_create_artwork() and self._is_league(league, self._leagues_artwork):
                    # import web_pdb
                    # web_pdb.set_trace()
                    try:
                        from . import makeart
                        art_value = {
                            "league": league,
                            'logo_home': icon_home,
                            'logo_guest': icon_guest,
                            'logo_league': icon_league,
                            "home": home,
                            'guest': guest,
                            'weekday': makeart.weekday(self.time_to_local(date_utc), self._language),
                            'month': makeart.month(self.time_to_local(date_utc), self._language),
                            'time': makeart.time(self.time_to_local(date_utc)),
                        }

                        art = makeart.ArtWork(self.dir('font'),
                                              os.path.join(self.dir('data'), 'layout.json'),
                                              art_value,
                                              self.log)

                        theme_artwork = self.get_setting('theme_artwork')

                        file_art = os.path.join(self.dir('thumb'), '{}_{}_{}.png'.format(id_, theme_artwork, '{}'))

                        if theme_artwork == 0:  # Light
                            art.set_color_font([0, 0, 0])
                            art.set_background(os.path.join(self.dir('media'), 'light.png'))
                        elif theme_artwork == 1:  # Dark
                            art.set_background(os.path.join(self.dir('media'), 'dark.png'))
                        elif theme_artwork == 2:  # Blue
                            art.set_background(os.path.join(self.dir('media'), 'blue.png'))
                        elif theme_artwork == 3:  # Transparent
                            art.set_background(os.path.join(self.dir('media'), 'transparent.png'))
                        else:
                            self.logd('_parse_listing', 'error set artwork theme')

                        if self.get_setting('is_thumb'):
                            thumb = art.make_file(file_art.format('thumb'), 'thumb')
                            self.logd('_parse_listing', thumb)
                        if self.get_setting('is_fanart'):
                            # art.set_background_type('fanart', self.fanart)
                            fanart = art.make_file(file_art.format('fanart'), 'fanart')
                            self.logd('_parse_listing', fanart)
                        if self.get_setting('is_poster'):
                            poster = art.make_file(file_art.format('poster'), 'poster')
                            self.logd('_parse_listing', poster)

                    except ImportError as e:
                        self.logd('ArtWork', 'ImportError [{}]'.format(str(e)))
                        xbmcgui.Dialog().notification(self.name,
                                                      'ImportError, creation ArtWork is not possible!',
                                                      self.icon, 3000)
                        import_error = True

                    except Exception as e:
                        self.logd('ArtWork', 'ERROR [{}]'.format(str(e)))

                if thumb:
                    icon = thumb
                else:
                    thumb = icon

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
                item['icon_home'] = icon_home
                item['home'] = home
                item['icon_guest'] = icon_guest
                item['guest'] = guest
                item['date_links'] = None
                item['url_links'] = url_links
                if 'href' is not item:
                    item['href'] = []

                self.log('ADD MATCH - %s' % item)

                if progress:
                    still = still - 1
                    fill = 100 - int(100 * float(still) / total)
                    progress.update(fill, message=game)

            except Exception as e:
                self.logd('_parse_listing', 'ERROR - %s' % str(e))

        return listing

    def _parse_links(self, id_, html):
        """
        Парсим страницу для списка ссылок
        :param html:
        :return: список словарей
        """

        def td_class_text(tr, ntag):
            try:
                return tr.find('td', {'class': ntag}).text
            except:
                return ''

        links = []

        json_data = json.loads(html)

        links.append({
            'data': {
                'broadcast_status': json_data.get('broadcast_status', None),
                'events': json_data.get('events', None),
                'lang': json_data.get('lang', None)
            },
            'status': 'data',
            'label': ''
        })

        broadcast = json_data.get('broadcast', None)

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
                        # href = self._resolve_direct_link(tr.find('a')['href'])
                        href = tr.find('a')['href']
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
        reviews = json_data.get('reviews', None)
        if reviews is not None:
            links.append({
                'label': '[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('REVIEWS:')),
                'status': 'title'
            })

            home = self.get(id_, 'home')
            guest = self.get(id_, 'guest')
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
        eventsstat = json_data.get('eventsstat', None)
        if eventsstat is not None:
            links.append({
                'label': '[COLOR FF0084FF][B]{}[/B][/COLOR]'.format(_('STATISTICS:')),
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
        if not links:
            return []

        title = self.get(id_, 'label')
        data = links[0]['data']

        scorel = '' if data['events'] is None else data['events'][0]
        scorer = '' if data['events'] is None else data['events'][1]

        # info_mini = self._get_mini_info_math(self.get(id_, 'id_event'))
        # plot = u'%s\n%s\n%s\n\n[B]                  %s  :  %s[/B]' % (
        #     self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
        #     self.get(id_, 'league'),
        #     self.get(id_, 'label'),
        #     info_mini['scorel'],
        #     info_mini['scorer']
        # )
        if self.get(id_, 'home'):
            plot = u'%s\n%s\n%s\n\n[B]                  %s  :  %s[/B]' % (
                self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
                self.get(id_, 'league'),
                self.get(id_, 'label'),
                scorel,
                scorer
            )
        else:
            plot = u'%s\n%s' % (self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
                self.get(id_, 'league'))

        l = []

        art = {
            'icon': self.get(id_, 'icon'),
            'thumb': self.get(id_, 'thumb'),
            'poster': self.get(id_, 'poster'),
            'fanart': self.get(id_, 'fanart'),
        }

        l.append({'label': u'{}       {}'.format(self.time_to_local(self.get(id_, 'date')).strftime('%d.%m %H:%M'),
                                                 self.get(id_, 'league')),
                  'info': {'video': {'title': title, 'plot': plot}},
                  'art': art,
                  'url': '',
                  'is_playable': False,
                  'is_folder': False})

        # l.append({'label': u'[B]{}    {} : {}    {} [/B]'.format(self.get(id_, 'home'), info_mini['scorel'],
        #                                                          info_mini['scorer'], self.get(id_, 'guest')),
        #           'info': {'video': {'title': title, 'plot': plot}},
        #           'art': art,
        #           'url': '',
        #           'is_playable': False,
        #           'is_folder': False})
        if self.get(id_, 'home'):
            l.append({'label': u'[B]{}    {} : {}    {} [/B]'.format(self.get(id_, 'home'), scorel, scorer,
                                                                     self.get(id_, 'guest')),
                      'info': {'video': {'title': title, 'plot': plot}},
                      'art': art,
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
                              'art': art,
                              'url': self.get_url(action='play', href=link['href'], id=id_),
                              'is_playable': True})
            elif link['status'] == 'info' or link['status'] == 'title':
                l.append({'label': link['label'],
                          'info': {'video': {'title': title, 'plot': plot}},
                          'art': art,
                          'url': '',
                          'is_playable': False,
                          'is_folder': False})
            else:
                pass

        if len(l) < 4:
            l.append({'label': _('Stream information will be available 30 minutes prior to the begining of an event.'),
                      'info': {'video': {'title': self._site, 'plot': self._site}},
                      'art': art,
                      'url': self.get_url(action='play', href=URL_NOT_LINKS, id=id_),
                      'is_playable': True})

        return l

    def _get_listing(self, params=None):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        self.update()

        filter_ = params['sort']

        listing = []

        now_utc = self.time_now_utc()

        self.logd('_get_listing() time_to_local(now_utc)', '%s' % self.time_to_local(now_utc))

        center = self._get_match_center_mini()

        try:
            for item in list(self._listing.values()):

                info_match = self._get_mini_info_math(item['id_event'], center)

                if not info_match:
                    self.logd('_get_listing() if not info_match', item['label'])
                    continue

                # import web_pdb
                # web_pdb.set_trace()

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
                # self.logd('_get_listing() {}'.format(item['label']), '%s' % item['date'])
                if info_match['status'] == 'OFFLINE':
                    dt = now_utc - date_
                    plot = self._format_timedelta(dt, _('Offline'))
                elif info_match['status'] == 'LIVE':
                    dt = now_utc - date_
                    plot = u'%s %s мин.' % (_('Live'), int(dt.total_seconds() / 60))
                else:
                    dt = date_ - now_utc
                    plot = self._format_timedelta(dt, _('After'))

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, self.time_to_local(date_).strftime('%d.%m %H:%M'), item['label'], item['league'])

                if info_match is not None and (info_match['status'] == u'OFFLINE' or info_match['status'] == u'LIVE'):
                    if item['home']:
                        lab = u'[B]{} - {}[/B]  {}'.format(info_match['scorel'], info_match['scorer'], info_match['status'])
                    else:
                        lab = u'{}'.format(info_match['status'])


                    if info_match['status'] == 'OFFLINE':
                        status = 'FF999999'
                    elif info_match['status'] == 'LIVE':
                        status = 'FFFF0000'
                else:
                    lab = self.time_to_local(date_).strftime('%d.%m %H:%M' if self.get_setting('is_date_item') else '%H:%M')

                label = '[COLOR %s]%s[/COLOR] - [B]%s[/B]    %s' % (
                    status, lab, item['label'], item['league'] if self.get_setting('is_league_item') else '')

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
