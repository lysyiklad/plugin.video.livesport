# -*- coding: utf-8 -*-

import xbmcgui
import xbmc

from resources.lib.livesport import LiveSport

plugin = LiveSport()

#_ = plugin.initialize_gettext()

@plugin.action()
def root(params):    
    return plugin.create_listing_()


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
def select_matches(params):    
    plugin.select_matches(params)


if __name__ == '__main__':
    plugin.run()
