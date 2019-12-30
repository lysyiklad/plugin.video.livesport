# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import object
import os
#import urllib.request, urllib.error, urllib.parse
import requests
import io
from PIL import Image, ImageDraw, ImageFont
import datetime
from collections import namedtuple

# locale.setlocale(locale.LC_ALL, '')

MAX_LENGTH_TEXT = 370

WEEKDAY = [u"Понедельник", u"Вторник", u"Среда",
           u"Четверг", u"Пятница", u"Суббота", u"Воскресенье"]

MONTHS = [u"января", u"февраля", u"марта", u"апреля", u"мая", u"июня", u"июля", u"августа",
          u"сентября", u"октября", u"ноября", u"декабря"]

SPECIFIC_ARTWORK_DATA = namedtuple('SPECIFIC_ARTWORK_DATA', [
    'league',
    'com_home',
    'vs',
    'com_away',
    'weekday',
    'month',
    'time',
    'size',
    'pos_home',
    'pos_away',
    'size_font_league',
    'size_font_command',
    'size_font_time',
    'size_font_weekday',
])

ARTWORK_DATA = {
    'poster': SPECIFIC_ARTWORK_DATA(25, 300, 365, 410, 530, 575, 645, (150, 150), (50, 100), (270, 100), 40, 55, 60,
                                    35),
    'thumb': SPECIFIC_ARTWORK_DATA(10, 220, None, 280, 335, 380, 420, (120, 120), (70, 80), (290, 80), 25, 40, 55, 35),
    'fanart': SPECIFIC_ARTWORK_DATA(None, None, None, None, None, None, None, (400, 400), (190, 150), (690, 150), 0, 0,
                                    0, 0),
    # 'fanart': SPECIFIC_ARTWORK_DATA(None, None, None, None, None, None, None, (250, 250), (100, 100), (460, 100), 0, 0, 0, 0),
}


def _cuttext(text, font, maxlength_text=MAX_LENGTH_TEXT):
    w, h = font.getsize(text)
    if w > maxlength_text:
        for i, ch in enumerate(text):
            w, h = font.getsize(text[0:i])
            if w > maxlength_text:
                text = text[0:i]
                text += '...'
                break
    return text


def _get_indent_left_for_center(text, width_frame, font):
    w, h = font.getsize(text)
    return int((width_frame - w) / 2)


# def _http_get_image(url):
#     """
#     :param url:
#     :return:
#     """
#     try:
#         req = urllib.request.Request(url=url)
#         req.add_header('User-Agent',
#                        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko')
#         req.add_header('Content-Type',
#                        'image/png')
#
#         resp = urllib.request.urlopen(req, timeout=10)
#         http = resp.read()
#         resp.close()
#         return http
#     except Exception as e:
#         raise Exception('ERROR GET HTTP LOGO [%s] - %s' % (e, url))
#
#
# def _open_url_image(url):
#     fd = _http_get_image(url)
#     image_file = io.BytesIO(fd)
#     image_file.seek(0)
#     ic1 = Image.open(image_file)
#     return ic1

def _get_http_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
    return requests.get(url, headers=headers).content


class ArtWorkFootBall(object):

    def __init__(self, plugin, **kwargs):
        self._plugin = plugin
        self._data = kwargs
        self.color_font = (0, 0, 0)
        # dark light transparent
        self._theme = 'light'
        self.language = 'English'  # Russian English

    def log(self, msg):
        if self._plugin is not None:
            self._plugin.logd('ArtWorkFootBall', msg)

    @property
    def plugin(self):
        return self._plugin

    @property
    def league(self):
        return self._data['league']

    @property
    def weekday(self):
        if self.language == 'Russian':
            return WEEKDAY[self._data['date'].weekday()]
        else:
            return self._data['date'].strftime('%A')

    @property
    def month(self):
        if self.language == 'Russian':
            return u'%s %s %s' % (self._data['date'].day, MONTHS[self._data['date'].month - 1], self._data['date'].year)
        else:
            return self._data['date'].strftime('%H %B %Y')

    @property
    def time(self):
        return self._data['date'].strftime("%H:%M")

    @property
    def vs(self):
        return 'vs'

    @property
    def logo_home(self):
        return self._data['logo_home']

    @property
    def logo_away(self):
        return self._data['logo_away']

    def file(self, type):
        return os.path.join(self.plugin.dir('thumb'), '%s_%s.png' % (type, str(self._data['id'])))

    def font(self, file, size):
        return ImageFont.truetype(os.path.join(self.plugin.dir('font'), file), size)

    @property
    def theme(self):
        return self._theme

    def _draw_text(self, draw, text, font, padding_top):
        if padding_top is None:
            return
        width_bkg = draw.im.size[0]
        text = _cuttext(text, font)
        draw.text((_get_indent_left_for_center(text, width_bkg, font),
                   padding_top), text, self.color_font, font=font)

    def _paste_logo(self, type, ifon):
        try:
            # ihome = _open_url_image(self.logo_home)
            # iaway = _open_url_image(self.logo_away)
            ihome = Image.open(io.BytesIO(_get_http_content(self.logo_home)))
            iaway = Image.open(io.BytesIO(_get_http_content(self.logo_away)))
        except Exception as e:
            self.log('ERROR PASTE LOGO [%s] - %s - %s' %
                     (e, self.logo_home, self.logo_away))
            ihome = Image.open(self.plugin.icon)
            iaway = Image.open(self.plugin.icon)
            # ic2.thumbnail(ARTWORK_DATA[type]['size_thumbaway'], Image.ANTIALIAS)
        ihome = ihome.convert("RGBA")
        iaway = iaway.convert("RGBA")
        art = ARTWORK_DATA[type]
        ihome = ihome.resize(art.size, Image.ANTIALIAS)
        iaway = iaway.resize(art.size, Image.ANTIALIAS)
        ifon.paste(ihome, art.pos_home, ihome)
        ifon.paste(iaway, art.pos_away, iaway)

    def _create_art(self, type_, background=None):

        file = self.file(type_)
        if os.path.exists(file):
            self.log('exists -%s' % file)
            return file
        try:
            # import web_pdb
            # web_pdb.set_trace()

            art = ARTWORK_DATA[type_]

            if background is None:
                background = os.path.join(self.plugin.dir('media'), '%s_%s.png' % (self.theme, type_))

            ifon = Image.open(background)
            ifon = ifon.convert("RGBA")
            draw = ImageDraw.Draw(ifon)

            self._draw_text(draw, self.league, self.font(
                'ubuntu_condensed', art.size_font_league), art.league)
            self._draw_text(draw, self._data['home'], self.font(
                'bandera_pro', art.size_font_command), art.com_home)
            self._draw_text(draw, self.vs, self.font(
                'ubuntu', art.size_font_weekday), art.vs)
            self._draw_text(draw, self._data['away'], self.font(
                'bandera_pro', art.size_font_command), art.com_away)
            self._draw_text(draw, self.weekday, self.font(
                'ubuntu', art.size_font_weekday), art.weekday)
            self._draw_text(draw, self.month, self.font(
                'ubuntu', art.size_font_weekday), art.month)
            self._draw_text(draw, self.time, self.font(
                'bandera_pro', art.size_font_time), art.time)

            self._paste_logo(type_, ifon)

            ifon.save(file)
            return file
        except Exception as e:
            self.log('ERROR CREATE ART [%s] - %s' % (e, file))
            return ''

    def create_poster(self, background=None):
        return self._create_art('poster', background)

    def create_thumb(self, background=None):
        return self._create_art('thumb', background)

    def create_fanart(self, background=None):
        fanart = self._create_art('fanart', background)
        return fanart

    def set_dark_theme(self):
        self._theme = 'dark'
        self.color_font = (255, 255, 255)

    def set_light_theme(self):
        self._theme = 'light'
        self.color_font = (0, 0, 0)

    def set_transparent_theme(self):
        self._theme = 'transparent'
        self.color_font = (255, 255, 255)

    def set_blue_theme(self):
        self._theme = 'blue'
        self.color_font = (255, 255, 255)
