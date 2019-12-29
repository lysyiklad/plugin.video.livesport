# -*- coding: utf-8 -*-

import os
import xbmc

from resources.lib.livesport import plugin

# Настройки после которых требуется обновление данных
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


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        if not xbmc.Player().isPlaying() and plugin.get_setting('is_update_service'):
            plugin.log('START BACKGROUND DATA UPDATE!')
            plugin.update()
            plugin.log('STOP BACKGROUND DATA UPDATE!')
        if monitor.waitForAbort(plugin.get_setting('scan_service') * 60):
            break
