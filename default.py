# -*- coding: utf-8 -*-

# import xbmcgui
import xbmc
import xbmcaddon

from resources.lib.livesport import plugin

FOLDER = ('', 'live', 'football', 'hockey', 'basketball', 'tennis', 'american_football', 'race', 'boxing', 'offline')

@plugin.action()
def root(params):
    folder_default = plugin.get_setting('folder_default')
    if xbmc.getInfoLabel('Container.FolderName') != plugin.name and folder_default and plugin._handle > 0:
        import xbmcplugin
        xbmcplugin.endOfDirectory(plugin._handle)
        xbmc.executebuiltin(
            'ActivateWindow(videos,"plugin://plugin.video.livesport/?action=listing&sort=%s", true])' % FOLDER[
                folder_default])
        return None
    return plugin.create_listing_categories()


@plugin.action()
def extra():
    return plugin.create_listing_extra()


@plugin.action()
def listing(params):
    # xbmcgui.Dialog().notification(
    #     plugin.name, str(params), xbmcgui.NOTIFICATION_INFO, 1000)
    return plugin.create_listing_filter(params=params)


@plugin.action()
def links(params):
    return plugin.get_links(params)


@plugin.action()
def play(params):
    return plugin.play(params)


@plugin.action()
def reset():
    return plugin.reset()


@plugin.action()
def select_leagues():
    plugin.selected_leagues()


@plugin.action()
def select_leagues_artwork():
    plugin.selected_leagues_artwork()


@plugin.action()
def settings():
    xbmcaddon.Addon().openSettings()


if __name__ == '__main__':
    # import web_pdb
    # web_pdb.set_trace()
    plugin.run()
