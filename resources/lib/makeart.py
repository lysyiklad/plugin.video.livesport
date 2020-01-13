# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import object
import os
import requests
import io
import json
import copy
from PIL import Image, ImageDraw, ImageFont

# import xbmcaddon
# __addon__ = xbmcaddon.Addon()
# FOLDER_FONT = os.path.join(__addon__.getAddonInfo('path'), 'resources', 'data', 'font')
# LAYOUT_JSON = os.path.join(__addon__.getAddonInfo('path'), 'resources', 'data', 'layout.json')

MAX_LENGTH_TEXT = 370

WEEKDAY = [u"Понедельник", u"Вторник", u"Среда",
           u"Четверг", u"Пятница", u"Суббота", u"Воскресенье"]

MONTHS = [u"января", u"февраля", u"марта", u"апреля", u"мая", u"июня", u"июля", u"августа",
          u"сентября", u"октября", u"ноября", u"декабря"]


def cuttext(text, font, maxlength_text=MAX_LENGTH_TEXT):
    w, h = font.getsize(text)
    if w > maxlength_text:
        for i, ch in enumerate(text):
            w, h = font.getsize(text[0:i])
            if w > maxlength_text:
                text = text[0:i]
                text += '...'
                break
    return text


def get_indent_left_for_center(text, width_frame, font):
    w, h = font.getsize(text)
    return int((width_frame - w) / 2)


def draw_text(draw, text, font, x, y, color=(255, 255, 255)):
    width_bkg = draw.im.size[0]
    text = cuttext(text, font)
    if x is None:
        draw.text((get_indent_left_for_center(text, width_bkg, font), y), text, color, font=font)
    else:
        draw.text((x, y), text, color, font=font)


def get_http_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}
    return requests.get(url, headers=headers).content


def load_logo(value):
    try:
        if os.path.exists(value):
            logo = Image.open(value)
        else:
            logo = Image.open(io.BytesIO(get_http_content(value)))
    except Exception as e:
        return None
    logo = logo.convert("RGBA")
    return logo


def paste_logo(img, logo, size, pos):
    try:
        logo = logo.resize(tuple(size), Image.ANTIALIAS)
        img.paste(logo, tuple(pos), logo)
    except:
        pass


def weekday(date, language):
    if language == 'Russian':
        return WEEKDAY[date.weekday()]
    else:
        return date.strftime('%A')


def month(date, language):
    if language == 'Russian':
        return u'%s %s %s' % (date.day, MONTHS[date.month - 1], date.year)
    else:
        return date.strftime('%H %B %Y')


def time(date):
    return date.strftime("%H:%M")


class ArtWork(object):
    LAYOUT_ARTWORK = None
    #backgrounds = {}

    def __init__(self, folder_font, layout_json, data_, log=None):
        assert os.path.exists(layout_json)
        self._folder_font = folder_font
        if ArtWork.LAYOUT_ARTWORK is None:
            with open(layout_json, "r") as f:
                ArtWork.LAYOUT_ARTWORK = json.load(f)

        assert ArtWork.LAYOUT_ARTWORK

        self._data = data_
        self._layout = copy.deepcopy(ArtWork.LAYOUT_ARTWORK)
        self._images = {}
        self._log = log

    def log(self, msg):
        if self._log is not None:
            self._log('<ArtWork>  {}'.format(msg))

    def get_background_type(self, type):
        return self._layout[type]['background']

    def set_background_type(self, type, data):
        self._layout[type]['background'] = data

    def set_color_font_type(self, type, data):
        self._layout[type]['color_font'] = data

    def set_size(self, type, data):
        self._layout[type]['size'] = data

    def set_background(self, data):
        for key, value in self._layout.items():
            value['background'] = data

    def set_color_font(self, data):
        for key, value in self._layout.items():
            value['color_font'] = data

    def get_value(self, type, key):
        return [a for a in self._layout[type]['data'] if a['key'] == key][0]

    def get_data(self, type, key, value):
        return self.get_value(type, key)[value]

    def set_data(self, type, key, value, data):
        self.get_value(type, key)[value] = data

    def make_file(self, file, type):

        if os.path.exists(file):
            self.log('exists - {}'.format(file))
            return file

        artwork = self._layout[type]

        self.log(artwork)
        self.log('make_file 1')

        try:
            background = artwork['background']
            self.log('make_file background {}'.format(background))
            # if background not in self.backgrounds:
            #     img = Image.open(background)
            #     self.backgrounds[background] = img
            # else:
            #     img = self.backgrounds[background]
            img = Image.open(background)
            if artwork['size'] is not None:
                img = img.resize(tuple(artwork['size']), Image.ANTIALIAS)
            self.log('make_file img {}'.format(img))
        except:
            img = Image.new('RGBA', tuple(artwork['size']), color='black')
            self.log('make_file except img {}'.format(img))

        draw = ImageDraw.Draw(img)

        self.log('make_file draw - {}'.format(draw))

        for art in artwork['data']:
            if art['key'] not in self._data and 'data' not in art:
                continue
            if art.get('data', None) is not None:
                value = art['data']
            else:
                value = self._data[art['key']]
            if art['type'] == 'text':
                self.log('make_file text - {}'.format(value))
                font = ImageFont.truetype(os.path.join(self._folder_font, art['font']), art['size'])
                self.log('make_file text - {}'.format(font))
                color = tuple(art['color'] if art['color'] is not None else artwork['color_font'])
                self.log('make_file text - {}'.format(color))
                draw_text(draw, value, font, art['x'], art['y'], color)
            elif art['type'] == 'picture':
                self.log('make_file picture - {}'.format(value))
                if value not in self._images:
                    logo = load_logo(value)
                    self._images[value] = logo
                else:
                    logo = self._images[value]
                self.log('make_file picture - {}'.format(logo))
                self.log('make_file picture - {}'.format(art['size']))
                self.log('make_file picture - {}'.format(art['pos']))
                paste_logo(img, logo, art['size'], art['pos'])
            else:
                continue

        img.save(file)
        return file
