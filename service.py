# -*- coding: utf-8 -*-

import os
import xbmc
# mport xbmcgui
import xbmcaddon


from default import plugin
#from resources.lib.plugin import Plugin


# Настройки после которых требуется обновление данных
SETTING_UPDATE = [
    'url_site',
    'time_zone_site',
    'is_thumb',
    'is_pars_links',
    'is_noold_item',    
]


class Monitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self._settings = self._get_settings()

    def _get_settings(self):
        noupdate = {}
        for name_setting in SETTING_UPDATE:
            #noupdate[name_setting] = plugin.get_setting(name_setting)
            noupdate[name_setting] = xbmcaddon.Addon().getSetting(name_setting)
        return noupdate

    def onSettingsChanged(self):
        super(Monitor, self).onSettingsChanged()
        
        # new_settings = self._get_settings()
        # if new_settings != self._settings:
        #     print 'NNNNNNNNNNNNNNNNNNNNNNNNNN %s' % new_settings['is_thumb']
        #     print 'OOOOOOOOOOOOOOOOOOOOOOOOOO %s' % self._settings['is_thumb']
        #     if new_settings['is_thumb'] != self._settings['is_thumb']:
        #         xbmc.sleep(1000)
        #         plugin.reset()
        #     else:
        #         plugin.on_settings_changed()
        #     self._settings = new_settings
        #     xbmc.executebuiltin('Container.Refresh()')

        plugin.on_settings_changed()
        xbmc.executebuiltin('Container.Refresh()')


if __name__ == "__main__":
    monitor = Monitor()
    while not monitor.abortRequested():
        if not xbmc.Player().isPlaying():
            plugin.log('START SERVICE!')
            plugin.update()
            plugin.log('STOP SERVICE!')
        if monitor.waitForAbort(plugin.get_setting('scan_service') * 60):
            break
