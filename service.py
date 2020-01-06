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
    STEP = 1

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()
        self._timeout_update = 0

        self.is_dlg = False
        self.showing = False
        self.window = xbmcgui.Window(WINDOW_FULLSCREEN_VIDEO)
        self.background = None
        self.list_left = None
        self.list_right = None
        self._id = None

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
        self._timeout_update += Monitor.STEP
        if not xbmc.Player().isPlaying():
            if self._timeout_update > plugin.get_setting('scan_service') * 60:
                plugin.log('START BACKGROUND DATA UPDATE!')
                plugin.update()
                plugin.log('STOP BACKGROUND DATA UPDATE!')
                self._timeout_update = 0

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
                    self.background = xbmcgui.ControlImage(1, 1, 1, 1,
                                                           os.path.join(plugin.dir('media'), "background.png"))
                    self.window.addControl(self.background)

                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        self.background.setPosition(100, 150)
                        self.background.setWidth(widht - 200)
                        self.background.setHeight(height - 640)
                        row = 26
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.background.setPosition(100, 100)
                        self.background.setWidth(widht - 200)
                        self.background.setHeight(height - 200)
                        row = 28
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.background.setPosition(50, 50)
                        self.background.setWidth(widht - 100)
                        self.background.setHeight(height - 100)
                        row = 20

                if self.list_left is None and self.list_right is None:
                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        self.list_left = xbmcgui.ControlList(100, 170, (widht - 200) / 2, height - 500, font='font10')
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.list_left = xbmcgui.ControlList(100, 110, int((widht - 200) / 2), height - 200,
                                                             font='font10')
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.list_left = xbmcgui.ControlList(50, 50, (widht - 100) / 2, height - 100, font='font10')
                    # self.list_left.setItemHeight(21)
                    # print 'self.list_left.getItemHeight() %s' % self.list_left.getItemHeight()
                    self.window.addControl(self.list_left)

                    if self._id is None:
                        status = []
                    else:
                        status = plugin.get_labels_status_match(self._id)
                    #status = []

                    if len(status) < row:
                        self.list_left.addItems(status)
                    else:
                        self.list_left.addItems(status[:row])

                    if widht == 1920 and height == 1440:  # WIDHT - 1920 HEIGHT 1440
                        self.list_right = xbmcgui.ControlList((widht - 200) / 2 + 150, 170, (widht - 200) / 2,
                                                              height - 500, font='font10')
                    elif widht == 1920 and height == 1080:  # SKIN RESOLUTION WIDHT - 1920 HEIGHT 1080
                        self.list_right = xbmcgui.ControlList(int((widht - 200) / 2) + 150, 110, int((widht - 200) / 2),
                                                              height - 200,
                                                              font='font10')
                    else:  # SKIN RESOLUTION WIDHT - 1280 HEIGHT 720
                        self.list_right = xbmcgui.ControlList((widht - 100) / 2 + 50, 50, (widht - 100) / 2,
                                                              height - 100,
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

    monitor = Monitor()

    while not monitor.abortRequested():

        monitor.show_fullscreen_video()

        monitor.update_data_plugin()

        if monitor.waitForAbort(Monitor.STEP):
            break
