# -*- coding: utf-8 -*-

import bs4
import urlparse
# import os
# import datetime
import requests

from collections import OrderedDict

from dateutil.parser import *
import dateutil
import time
import json

HEADERS_HTTP = {'User-Agent':
                    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0'
                    ' (compatible; MSIE 6.0; Windows NT 5.1; SV1) ; .NET CLR 1.1.4322; .NET CLR 2.0.50727; '
                    '.NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C)'}


def find_src(html, tag, quotes):
    i1 = html.find(quotes, html.find(tag))
    return html[i1 + 1:html.find(quotes, i1 + 1)]


def get_match_center_mini():
    try:
        center = requests.get(
            'https://moon.livesport.ws/engine/modules/sports/sport_template_loader.php?'
            'from=showfull&template=match/main_match_center_mini_refresher', headers=HEADERS_HTTP, timeout=10).content
    except Exception as e:
        return None

    center = center.decode('unicode-escape')
    center = center[center.find('{'):]

    if center:
        center = json.loads(center)
    else:
        return None
    return center


def get_mini_info_math(id_event, center=None):
    if center is not None:
        for info in center['match_center_mini']:
            if info['event'] == str(id_event):
                return info
    else:
        center = get_match_center_mini()
        return get_mini_info_math(id_event, center)
    return None


def parse_live():
    site = 'https://livesport.ws/en'

    html = requests.get(site, headers=HEADERS_HTTP, timeout=10).content

    direct = {}

    soup = bs4.BeautifulSoup(html, 'html.parser')

    tag_matchs = soup.findAll('li', {'itemtype': 'http://data-vocabulary.org/Event'})

    center = get_match_center_mini()

    from selenium import webdriver

    webdriver.DesiredCapabilities.PHANTOMJS[
        'phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
    driver = webdriver.PhantomJS()


    for tag_match in tag_matchs:

        tag_a = tag_match.find('a')

        # game = tag_a['title']

        id_ = int(tag_a['href'].split('/')[-1].split('-')[0])

        tag_i = tag_a.find('span', {'class': 'date'}).find('i')

        id_event = int(tag_i['id'].split('-')[1])

        info_match = get_mini_info_math(id_event, center)

        url_links = '{}/engine/modules/sports/sport_refresh.php?' \
                    'from=event&event_id={}&tab_id=undefined&post_id={}&lang=en'.format(
            site, id_event, str(id_))

        # url_links = '{}/engine/modules/sports/sport_refresh.php?' \
        #             'from=event&event_id={}&tab_id=undefined&post_id={}'.format(site, id_event, str(id_))

        # executable_path="/storage/.local/lib/phantomjs")
        while True:
            try:
                driver.get('http://bilasport.net/nhl/islanders.php')
                break
            except:
                print 'except'
                continue

        html = driver.page_source
        link = find_src(html, b'var sou', b'\"')
        #driver.quit()
        time.sleep(2)

        if info_match['status'] == 'LIVE':

            json_data = requests.get(url_links, headers=HEADERS_HTTP, timeout=10).json()

            broadcast = json_data.get('broadcast', None)

            if broadcast is not None:
                tag_broadcast = bs4.BeautifulSoup(broadcast, 'html.parser')
                tag_li = tag_broadcast.findAll('li')
                for i, li in enumerate(tag_li):
                    trs = li.find('table').find('tbody').findAll('tr')

                    for tr in trs:
                        tag_img = tr.find('img')
                        if i == 0:
                            link = ''
                            href = tr.find('a')['href']
                            h = requests.get(href, headers=HEADERS_HTTP, timeout=10).content
                            print('_resolve_direct_link - href %s' % href)
                            s = bs4.BeautifulSoup(h, 'html.parser')
                            tif = s.find('iframe')
                            src = tif['src']
                            print('_resolve_direct_link - iframe src %s' % src)
                            prs = urlparse.urlparse(src)
                            direct[href] = href
                            if prs.netloc == 'dummyview.online':
                                src_json = 'http://185.255.96.166:3007/api/streams/2/channels/' + prs.path.split('/')[-1]
                                print '_resolve_direct_link - src_json - %s' % src_json
                                data_json = requests.get(href, headers=HEADERS_HTTP, timeout=10).json()
                                print '_resolve_direct_link - data_json - %s' % data_json
                                src = data_json['data']['sourceUrl']
                                print '_resolve_direct_link - src - %s' % src
                                # if urlparse(src).netloc == 'ok.ru':
                                #     tok = bs4.BeautifulSoup(self.get_http(src).content, 'html.parser')
                                #     self.logd('_resolve_direct_link - ok.ru', tok)
                                #     do = json.loads(tok.find("div", {"data-options": re.compile(r".*")})['data-options'])
                                #     self.logd('_resolve_direct_link - data_options', do)
                                #     link = json.loads(do['flashvars']['metadata'])['hlsMasterPlaylistUrl']
                                # elif urlparse(src).netloc == 'rutube.ru':
                                #     link = src
                                # elif urlparse(src).netloc == 'box-live.stream':
                                #     # twiter ????
                                #     #self.log(self.get_http(src).content)
                                #     link = 'http://box-live.stream'
                                if urlparse.urlparse(src).netloc == 'bilasport.net':
                                    from selenium import webdriver

                                    webdriver.DesiredCapabilities.PHANTOMJS[
                                        'phantomjs.page.settings.userAgent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
                                    driver = webdriver.PhantomJS()  #executable_path="/storage/.local/lib/phantomjs")
                                    driver.get(src)
                                    html = driver.page_source
                                    link = find_src(html, b'var sou', b'\"')
                                    #driver.close()

                            if link:
                                direct[href] = link

    return direct


st = time.clock()
l = parse_live()
for li in l:
    print(li)
print(len(l))
print(time.clock() - st)
