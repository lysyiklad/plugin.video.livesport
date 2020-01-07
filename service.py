# -*- coding: utf-8 -*-

import os
import json
import xbmc
import xbmcgui
import datetime
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
    STEP = 1

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()

        self.is_dlg = False
        self.showing = False
        self.window = xbmcgui.Window(WINDOW_FULLSCREEN_VIDEO)
        self.background = None
        self.list_left = None
        self.list_right = None
        self._id = None
        self._date_update_service = None

        try:
            self._date_update_service = datetime.datetime.strptime(plugin.get_setting('date_update_service'),
                                                                   "%m/%d/%Y %H:%M")
        except:
            self._date_update_service = datetime.datetime.utcnow() - datetime.timedelta(
                minutes=(plugin.get_setting('scan_service') + 5))

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

    def update_data_plugin(self):
        if not plugin.get_setting('is_update_service'):
            return
        if not xbmc.Player().isPlaying():
            utcnow = datetime.datetime.utcnow()
            if int((utcnow - self._date_update_service).total_seconds() / 60) > int(plugin.get_setting('scan_service')):
                plugin.log('START BACKGROUND DATA UPDATE!')
                plugin.update()
                plugin.log('STOP BACKGROUND DATA UPDATE!')
                self._date_update_service = utcnow
                plugin.set_setting('date_update_service', utcnow.strftime("%m/%d/%Y %H:%M"))

    def onNotification(self, sender, method, data):
        plugin.log('ON NOTIFICATION %s - %s - %s' % (sender, method, data))
        #        xbmc.sleep(500)

        if sender == 'plugin.video.livesport':
            self.is_dlg = True
            command_info = json.loads(data)
            self._id = int(command_info['id'])
            plugin.log('ON NOTIFICATION SENDER %s' % command_info)

        if sender == 'xbmc':
            if method == 'Player.OnStop':
                self.is_dlg = False
                command_info = json.loads(data)
                self._id = None
                plugin.log('ON NOTIFICATION SENDER %s' % command_info)

    def _get_skin_resolution(self):
        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        try:
            res = tree.findall("./res")[0]
        except:
            res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])

    def show_fullscreen_video(self):
        if not plugin.get_setting('is_info_fullscreenvideo'):
            return
        if xbmc.getCondVisibility('Window.IsActive(videoosd)'):
            if self.is_dlg:
                widht, height = self._get_skin_resolution()
                row = 20
                if self.background is None:
                    plugin.log('SKIN RESOLUTION WIDHT - %s HEIGHT %s' % (widht, height))
                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        row = 26
                        pb = (100, 150, 200, 650)
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        row = 28
                        pb = (100, 100, 200, 200)
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        row = 20
                        pb = (50, 50, 100, 100)

                    self.background = xbmcgui.ControlImage(1, 1, 1, 1,
                                                           os.path.join(plugin.dir('media'), "background.png"))
                    self.window.addControl(self.background)
                    self.background.setPosition(pb[0], pb[1])
                    self.background.setWidth(widht - pb[2])
                    self.background.setHeight(height - pb[3])

                if self.list_left is None and self.list_right is None:
                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        pll = (100, 170, 200, pb[3])
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        pll = (100, 110, 200, pb[3])
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        pll = (50, 50, 100, pb[3])
                        # self.list_left.setItemHeight(5)
                    self.list_left = xbmcgui.ControlList(pll[0], pll[1], int((widht - pll[2]) / 2), height - pll[3],
                                                         font='font10')
                    self.window.addControl(self.list_left)

                    if self._id is None:
                        status = []
                    else:
                        status = plugin.get_labels_status_match(self._id)

                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        plr = (200, 150, 170, 200, pb[3])
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        plr = (200, 150, 110, 200, pb[3])
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        plr = (100, 50, 50, 100, pb[3])

                    self.list_right = xbmcgui.ControlList((widht - plr[0]) / 2 + plr[1], plr[2], (widht - plr[3]) / 2,
                                                          height - plr[4], font='font10')
                    self.window.addControl(self.list_right)

                    live = plugin.get_labels_live()

                    if len(status) <= row and len(live) <= row:
                        self.list_left.addItems(status)
                        self.list_right.addItems(live)
                    else:
                        if len(status) >= row:
                            self.list_left.addItems(status[:row])
                            self.list_right.addItems(status[row:] + live)
                        else:
                            r = row - len(status)
                            self.list_left.addItems(status + live[:r])
                            self.list_right.addItems(live[r:])

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

    monitor = Monitor()

    while not monitor.abortRequested():

        monitor.show_fullscreen_video()

        monitor.update_data_plugin()

        if monitor.waitForAbort(Monitor.STEP):
            break
