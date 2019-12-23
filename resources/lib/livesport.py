# -*- coding: utf-8 -*-

import datetime
import os
# from collections import OrderedDict
from urlparse import urlparse
import pickle
import json

# import xbmcgui

import bs4
import dateutil
from dateutil.parser import *
from dateutil.tz import tzlocal, tzoffset

from plugin import Plugin, _




# def _upper(t):
#     RUS = {u"А": u"а", u"Б": u"б", u"В": u"в", u"Г": u"г", u"Д": u"д", u"Е": u"е", u"Ё": u"ё",
#            u"Ж": u"ж", u"З": u"з", u"И": u"и", u"Й": u"й", u"К": u"к", u"Л": u"л", u"М": u"м",
#            u"Н": u"н", u"О": u"о", u"П": u"п", u"Р": u"р", u"С": u"с", u"Т": u"т", u"У": u"у",
#            u"Ф": u"ф", u"Х": u"х", u"Ц": u"ц", u"Ч": u"ч", u"Ш": u"ш", u"Щ": u"щ", u"Ъ": u"ъ",
#            u"Ы": u"ы", u"Ь": u"ь", u"Э": u"э", u"Ю": u"ю", u"Я": u"я"}

#     for i in RUS.keys():
#         t = t.replace(RUS[i], i)
#     for i in range(65, 90):
#         t = t.replace(chr(i + 32), chr(i))
#     return t



class LiveSport(Plugin):

    def __init__(self):
        super(LiveSport, self).__init__()
        if self._language != 'Russian':
            self._site = os.path.join(self._site, 'en')
        

    def create_listing_(self):
        #self.update()
        select_item = [{'label': '[UPPERCASE][COLOR FFFF0000][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Live')),
                        'url': self.get_url(action='reset_inter')}, 
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('All')),
                        'url': self.get_url(action='reset_inter')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Football')),
                        'url': self.get_url(action='create_listing_football')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Ice Hockey')),
                        'url': self.get_url(action='create_listing_hockey')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Basketball')),
                        'url': self.get_url(action='create_listing_football')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Tennis')),
                        'url': self.get_url(action='create_listing_football')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('American Football')),
                        'url': self.get_url(action='create_listing_football')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Race')),
                        'url': self.get_url(action='create_listing_football')},
                       {'label': '[UPPERCASE][COLOR FF0084FF][B]{}[/B][/COLOR][/UPPERCASE]'.format(_('Boxing')),
                        'url': self.get_url(action='create_listing_football')},
            
           
                       ]
        
        return select_item  #+ self.get_listing()

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
        i = 1
        # leagues = self._load_leagues()
        # selected_leagues = self._get_selected_leagues()

        listing = {}

        soup = bs4.BeautifulSoup(html, 'html.parser')

        tag_matchs = soup.findAll(
            'li', {'itemtype': 'http://data-vocabulary.org/Event'})

        i = 1

        for tag_match in tag_matchs:

            # date_away = tag_match.find('meta')['content']
            tag_a = tag_match.find('a')
            game = tag_a['title']
            id_ = int(tag_a['href'].split('/')[-1].split('-')[0])

            icon_sport = tag_a.find('span', {'class': 'sport'}).find('img')[
                'data-src']
            tag_i = tag_a.find('span', {'class': 'date'}).find('i')
            id_event = int(tag_i['id'].split('-')[1])

            url_links = '{}/engine/modules/sports/sport_refresh.php?' \
                        'from=event&event_id={}&tab_id=undefined&post_id={}'.format(
                            self._site, id_event, str(id_))

            date_naive = tag_i['data-datetime']
            try:
                dt = dateutil.parser.parse(date_naive)
            except ValueError as e:
                if e.message == 'hour must be in 0..23':
                    dt = dateutil.parser.parse(date_naive.split()[0])

            date_utc = self._time_naive_site_to_utc_aware(dt)

            tags_div = tag_a.find(
                'div', {'class': 'commands commands_match_center'}).findAll('div')

            if id_ not in listing:
                listing[id_] = {}
            item = listing[id_]
            item['id'] = id_
            item['id_event'] = id_event
            item['sport'] = os.path.basename(
                urlparse(icon_sport).path).split('.')[0]
            item['status'] = tag_i.text
            item['label'] = game
            item['league'] = tag_a.find('span', {'class': 'competition'}).text
            item['date'] = date_utc
            item['thumb'] = ''
            item['icon'] = icon_sport
            item['poster'] = ''
            item['fanart'] = self.fanart
            item['icon1'] = tags_div[1].contents[1]['data-src'].replace(
                '?18x18=1', '')
            item['command1'] = tags_div[0].text
            item['icon2'] = tags_div[1].contents[3]['data-src'].replace(
                '?18x18=1', '')
            item['command2'] = tags_div[2].text

            item['url_links'] = url_links
            if 'href' is not item:
                item['href'] = []

            self.logd(i, item)
            i += 1

        return listing

    def _parse_links(self, html):
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

            tag_broadcast = bs4.BeautifulSoup(broadcast, 'html.parser')

            tag_li = tag_broadcast.findAll('li')

            for i, li in enumerate(tag_li):
                if i == 0:
                    continue

                trs = li.find('table').find('tbody').findAll('tr')

                for tr in trs:

                    tag_img = tr.find('img')
                    links.append(
                        {
                            'icon': tag_img['src'],
                            'lang': tag_img['title'],
                            'speed': td_class_text(tr, 'speed'),
                            'channel': td_class_text(tr, 'channel'),
                            'fps': td_class_text(tr, 'fps'),
                            'format': td_class_text(tr, 'format'),
                            'href': tr.find('a')['href'],
                        }
                    )
        else:
            eventsstat = data.get('eventsstat', None)
            if eventsstat is not None:
                content = eventsstat[0].get('content', None)
                if content is not None:
                    tag_content = bs4.BeautifulSoup(content, 'html.parser')
                    if tag_content:
                        for tabl in tag_content.findAll('table'):
                            tags_td = tabl.findAll('td')
                            links.append({
                                'label': u'{}   {}   {}'.format(tags_td[0].text, tags_td[2].text, tags_td[4].text),
                            })

        return links

    def _get_links(self, id, links):
        """
        Возвращаем список ссылок для папки конкретного элемента
        :param id:
        :return:
        """

        title = self.get(id, 'label')
        info_mini = self._get_mini_info_math(self.get(id, 'id_event'))
        plot = u'%s\n%s\n%s\n[B]-------------   %s  :  %s   -------------[/B]' % (self.time_to_local(self.get(id, 'date')).strftime('%d.%m %H:%M'), 
                                                                                  self.get(id, 'league'),
                                                                                  self.get(id, 'label'),
                                                                                  info_mini['scorel'], 
                                                                                  info_mini['scorer'])

        l = []

        for link in links:

            if self.get(id, 'status') == u'OFFLINE' or 'href' not in link:
                l.append({'label': link['label'],
                          'info': {'video': {'title': title, 'plot': plot}},
                          'url': '',
                          'is_playable': False,
                          'is_folder': False})
            else:
                urlprs = urlparse(link['href'])

                if urlprs.scheme == 'acestream':
                    icon = os.path.join(self.dir('media'), 'ace.png')
                    label = '[COLOR FF00A550][AceStream][/COLOR]'
                elif urlprs.scheme == 'sop':
                    icon = os.path.join(self.dir('media'), 'sop.png')
                    label = '[COLOR FF42AAFF][ SopCast ][/COLOR]'
                    plot = plot + u'\n\nДля просмотра SopCast необходим плагин Plexus'
                else:
                    continue
                    label = 'flash'
                    icon = os.path.join(self.dir('media'), 'http.png')

                label = u'{} | {} | {} | {} ({})'.format(
                    label, link['speed'], link['channel'], link['format'], link['lang'])

                l.append({'label': label,
                          'info': {'video': {'title': title, 'plot': plot}},
                          'thumb': icon,
                          'icon': icon,
                          'fanart': '',
                          'art': {'icon': icon, 'thumb': icon, },
                          'url': self.get_url(action='play', href=link['href'], id=id),
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

    def create_listing_sport(self, sport):
        l = [{'label': '[COLOR FF0084FF][B]ВЫБРАТЬ ТУРНИРЫ[/B][/COLOR]', 'url': self.get_url(action='select_matches')},
             {'label': '[COLOR FF0084FF][B]ОБНОВИТЬ[/B][/COLOR]', 'url': self.get_url(action='reset_inter')}]
        return l + self._get_listing(sport=sport)


    def _get_listing(self, sport=None):
        """
        Возвращаем список для корневой виртуальной папки
        :return:
        """

        listing = []

        now_utc = self.time_now_utc()

        self.logd('_get_listing()', '%s' % self.time_to_local(now_utc))

        center = self._get_match_center_mini()

        try:
            for item in self._listing.values():

                if sport is not None and sport != item['sport']:
                    continue

                info_match = self._get_mini_info_math(item['id_event'], center)

                status = 'FFFFFFFF'

                date_ = item['date']
                if date_ > now_utc:
                    dt = date_ - now_utc
                    plot = self.format_timedelta(dt, u'Через')
                else:
                    dt = now_utc - date_
                    if int(dt.total_seconds() / 60) < 110:
                        plot = u'Прямой эфир %s мин.' % int(
                            dt.total_seconds() / 60)
                    else:
                        plot = self.format_timedelta(dt, u'Закончен')

                title = u'[COLOR %s]%s[/COLOR]\n[B]%s[/B]\n[UPPERCASE]%s[/UPPERCASE]' % (
                    status, self.time_to_local(date_).strftime('%d.%m %H:%M'), item['label'], item['league'])

                if info_match is not None and (info_match['status'] == u'OFFLINE' or info_match['status'] == u'LIVE'):
                    lab = u'{} - {}  {}'.format(
                        info_match['scorel'], info_match['scorer'], info_match['status'])
                    if info_match['status'] == 'OFFLINE':
                        status = 'FF999999'
                    elif info_match['status'] == 'LIVE':
                        status = 'FFFF0000'
                else:
                    lab = self.time_to_local(date_).strftime(
                        u'%d.%m %H:%M' if self.get_setting('is_date_item') else u'%H:%M')

                label = u'[COLOR %s]%s[/COLOR] - [B]%s[/B]    %s' % (status, lab, item['label'],
                                                                     item['league'] if self.get_setting(
                                                                         'is_league_item') else '')

                plot = title + '\n' + plot + '\n\n' + self._site

                href = ''

                if self.get_setting('is_play'):
                    for h in item['href']:
                        if h['title'] == self.get_setting('play_engine').decode('utf-8'):
                            href = h['href']
                            break

                is_folder, is_playable, get_url = self.geturl_isfolder_isplay(
                    item['id'], href)

                icon = item['icon']

                # for league_pictures in self.league_image:
                #     if league_pictures['league'] == item['league']:
                #         icon = league_pictures['src']

                listing.append({
                    'label': label,
                    'art': {
                        'thumb': '',
                        'poster': '',
                        'fanart': self.fanart,
                        'icon': icon,
                    },
                    'info': {
                        'video': {
                            # 'year': '',
                            'plot': plot,
                            'title': label,
                        }
                    },
                    'offscreen': False,
                    'is_folder': is_folder,
                    'is_playable': is_playable,
                    'url': get_url,
                })

        except Exception as e:
            self.logd('._get_listing() ERROR', str(e))

        return listing
