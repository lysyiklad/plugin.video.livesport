# -*- coding: utf-8 -*-

from resources.lib.livesport import LiveSport

plugin = LiveSport()

_ = plugin.initialize_gettext()

@plugin.action()
def root():
    return plugin.create_listing_()

@plugin.action()
def create_listing_football():
    return plugin.create_listing_sport(u'football')


@plugin.action()
def create_listing_hockey():
    return plugin.create_listing_sport(u'hockey')


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
def reset_inter():
    return plugin.create_listing_()


@plugin.action()
def select_matches(params):
    plugin.select_matches(params)


if __name__ == '__main__':
    plugin.run()
