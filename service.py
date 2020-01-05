# -*- coding: utf-8 -*-

import os
import json
import xbmc
import xbmcgui
import xml.etree.ElementTree as ET

from resources.lib.livesport import plugin

WINDOW_FULLSCREEN_VIDEO = 12005


SETTING_UPDATE = [
    'url_site',
    'time_zone_site',
    'is_thumb',
    'is_poster',
    'is_fanart',
    'theme_artwork',
    'is_pars_links',
    'is_noold_item',
    'is_http_link',
    'is_date_item',
    'is_league_item',
]

class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()

    def _get_settings(self):

        noupdate = {}
        for name_setting in SETTING_UPDATE:
            noupdate[name_setting] = plugin.get_setting(name_setting)
            # noupdate[name_setting] = xbmcaddon.Addon().getSetting(name_setting)
        return noupdate

    def onSettingsChanged(self):
        super(Monitor, self).onSettingsChanged()
        xbmc.sleep(500)
        new_settings = self._get_settings()
        if new_settings != self._settings:
            plugin.on_settings_changed()
            self._settings = new_settings

# status = [
# u'04.01 16:00',
# u'04.01 16:00       Россия. КХЛ',
# u'[B]ХК Сочи    1 : 1    ХК ЦСКА [/B]',
# u'[COLOR FF0084FF][B]ТРАНСЛЯЦИИ:[/B][/COLOR]',
# u'[COLOR FF0084FF][B]ОБЗОР:[/B][/COLOR]',
# u'1-й период (0:1)',
# u'ХК Сочи    17:51   [COLOR FFFFFF00][B][ 2 ][/B][/COLOR]   Лугин Д. (Игра высоко поднятой клюшкой)',
# u'ХК ЦСКА    19:47   [COLOR FFFF0000][B]ГОЛ[/B][/COLOR]    Киселевич Б. + Окулов К. Секач И.',
# u'2-й период (1:0)',
# u'ХК Сочи    01:11   [COLOR FFFF0000][B]ГОЛ[/B][/COLOR]   Шмелев С. Абросимов Р. + Мосалев Д.',
# u'ХК ЦСКА    05:48   [COLOR FFFFFF00][B][ 2 ][/B][/COLOR]   (Задержка клюшкой) Марченко А.',
# u'ХК Сочи    10   [COLOR FFFFFF00][B][ 2 ][/B][/COLOR]',
# u'[COLOR FF0084FF][B]СТАТИСТИКА:[/B][/COLOR]',
# u'10  -   Броски в створ ворот   -  13',
# u'10% (1/10)  -   % реализов. бросков   -  7.69% (1/13)',
# u'6  -   Блок-но ударов   -  4',
# u'12  -   Отраженные броски   -  9',
# u'92.31% (12/13)  -   % отраженных бросков   -  90% (9/10)',
# u'1  -   Удаления   -  1',
# u'4  -   Штрафное время   -  2',
# u'0  -   Шайбы в большинстве   -  1',
# u'1  -   Шайбы в меньшинстве   -  0',
# u'0% (0/1)  -   % реализ. большинства   -  100% (1/1)',
# u'0% (0/1)  -   % игры в меньшинстве   -  100% (1/1)',
# u'3  -   Силовые приемы   -  3',
# u'9  -   Выигр. вбрасывания   -  13',
# u'40.91  -   Вбрасывания %   -  59.09',
# u'0  -   Голы в пустые ворота   -  0',
# u'29',
# u'30',
# u'31',
# u'32',
# u'33',
# u'34',
# u'35',
# ]
#
# live = [u'[UPPERCASE][COLOR FF0084FF][B]Прямой эфир:[/B][/COLOR][/UPPERCASE]',
# u'[B]1 - 1[/B]  ХК Сочи - ХК ЦСКА',
# u'[B]0 - 0[/B]  Хетафе - Реал Мадрид',
# u'[B]0 - 0[/B]  Понферрадина - Кадис',
# u'[B]0 - 0[/B]  ХК Динамо Рига - ХК Барыс',
# u'[B]0 - 0[/B]  Кардифф - Карлайл Юнайтед',
# u'[B]0 - 0[/B]  Брентфорд - Сток Сити',
# u'[B]0 - 0[/B]  Фулхэм - Астон Вилла',
# u'[B]0 - 0[/B]  Брайтон - Шеффилд Уэнсдей',
# u'[B]0 - 0[/B]  Уотфорд - Транмир Роверс',
# u'[B]0 - 0[/B]  Саутгемптон - Хаддерсфилд',
# u'[B]0 - 0[/B]  Рединг - Блэкпул',
# u'[B]0 - 0[/B]  Престон - Норвич',
# u'[B]0 - 0[/B]  Оксфорд Юнайтед - Хартлпул Юнайтед'
# ]



class MonitorFullScreenVideo(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.is_dlg = False
        self.showing = False
        self.window = xbmcgui.Window(WINDOW_FULLSCREEN_VIDEO)
        self.background = None
        self.list_left = None
        self.list_right = None
        self._id = None

    def onNotification(self, sender, method, data):
        '''builtin function for the xbmc.Monitor class'''
        print 'NOTIFICATION %s - %s - %s' % (sender, method, data)

        if sender == plugin.id:
            self.is_dlg = True
            command_info = json.loads(data)
            self._id = int(command_info['id'])
            print 'NOTIFICATION SENDER %s' % command_info
            print 'NOTIFICATION SENDER %s' % str(self.is_dlg)

        if sender == 'xbmc':
            if method == 'Player.OnStop':
                self.is_dlg = False
                command_info = json.loads(data)
                self._id = None
                print 'NOTIFICATION SENDER %s' % command_info
                print 'NOTIFICATION SENDER %s' % str(self.is_dlg)

    def _get_skin_resolution(self):
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try:
            res = tree.findall("./res")[0]
        except:
            res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])

    def show(self):
        if xbmc.getCondVisibility('Window.IsActive(videoosd)'):

            if self.is_dlg:
                widht, height = self._get_skin_resolution()
                row = 20
                if self.background is None:
                    print 'SKIN RESOLUTION WIDHT - %s HEIGHT %s' % (widht, height)
                    self.background = xbmcgui.ControlImage(1, 1, 1, 1, os.path.join(plugin.dir('media'), "background.png"))
                    self.window.addControl(self.background)

                    if widht == 1920 and height == 1440:    # WIDHT - 1920 HEIGHT 1440
                        self.background.setPosition(100, 150)
                        self.background.setWidth(widht - 200)
                        self.background.setHeight(height - 500)
                        row = 26
                    elif widht == 1920 and height == 1080:  #SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.background.setPosition(100, 100)
                        self.background.setWidth(widht - 200)
                        self.background.setHeight(height - 200)
                        row = 28
                    else:   # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.background.setPosition(50, 50)
                        self.background.setWidth(widht - 100)
                        self.background.setHeight(height - 100)
                        row = 20

                if self.list_left is None and self.list_right is None:
                    if widht == 1920 and height == 1440:    # WIDHT - 1920 HEIGHT 1440
                        self.list_left = xbmcgui.ControlList(100, 170, (widht - 200)/2, height - 500, font='font10')
                    elif widht == 1920 and height == 1080:  #SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.list_left = xbmcgui.ControlList(100, 110, int((widht-200)/2), height-200, font='font10')
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.list_left = xbmcgui.ControlList(50, 50, (widht - 100) / 2, height - 100, font='font10')
                        # self.list_left.setItemHeight(5)
                    self.window.addControl(self.list_left)

                    if self._id is None:
                        status = []
                    else:
                        status = plugin.get_labels_status_match(self._id)

                    if len(status) < row:
                        self.list_left.addItems(status)
                    else:
                        self.list_left.addItems(status[:row])

                    if widht == 1920 and height == 1440:    # WIDHT - 1920 HEIGHT 1440
                        self.list_right = xbmcgui.ControlList((widht - 200)/2 + 150, 170, (widht - 200)/2, height - 500, font='font10')
                    elif widht == 1920 and height == 1080:  #SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.list_right = xbmcgui.ControlList(int((widht-200)/2) + 150, 110, int((widht-200)/2), height-200,
                                                              font='font10')
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.list_right = xbmcgui.ControlList((widht - 100) / 2 + 50, 50, (widht - 100) / 2, height - 100,
                                                              font='font10')

                    self.window.addControl(self.list_right)

                    live = plugin.get_labels_live()

                    if len(status) < row:
                        self.list_right.addItems(live)
                    else:
                        self.list_right.addItems(status[row:] + live)

                self.showing = True
        else:
            if self.showing == True and self.background:

                if self.background is not None:
                    self.window.removeControl(self.background)
                    self.background = None
                if self.list_left is not None:
                    self.window.removeControl(self.list_left)
                    self.list_left = None
                if self.list_right is not None:
                    self.window.removeControl(self.list_right)
                    self.list_right = None

                self.showing = False


if __name__ == "__main__":

    # monitor = Monitor()
    #
    # while not monitor.abortRequested():
    #     if not xbmc.Player().isPlaying() and plugin.get_setting('is_update_service'):
    #         plugin.log('START BACKGROUND DATA UPDATE!')
    #         plugin.update()
    #         plugin.log('STOP BACKGROUND DATA UPDATE!')
    #     if monitor.waitForAbort(plugin.get_setting('scan_service') * 60):
    #         break

    monitor_12005 = MonitorFullScreenVideo()

    while not monitor_12005.abortRequested():

        monitor_12005.show()

        if monitor_12005.waitForAbort(1):
            break

