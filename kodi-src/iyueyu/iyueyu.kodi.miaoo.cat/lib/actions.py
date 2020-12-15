import xbmc
import xbmcgui
import urllib
import functools
import xbmcaddon
import re
from bs4 import BeautifulSoup
from urlparse import urljoin
from resolveurl.lib.net import get_ua
from lib import config, common, scrapers, store, cleanstring, cache

actions = []
def _action(func):
    '''Decorator
    Mark the function as a valid action by
    putting the name of `func` into `actions`
    '''
    actions.append(func.__name__)
    return func

def _dir_action(func):
    '''Decorator
    Assumes `func` returns list of diritems
    Results from calling `func` are used to build plugin directory
    '''
    @_action # Note: must keep this order to get func name
    @functools.wraps(func)
    def make_dir(*args, **kargs):
        diritems = func(*args, **kargs)
        if not diritems:
            return
        for di in diritems:
            common.add_item(di)
        common.end_dir()
    return make_dir

@_dir_action
def index():
    return config.index_items

def _saved_to_list_context_menu(all_title, show_url, image):
    add_save_url = common.action_url('add_to_saved', all_title=all_title,
                                     show_url=show_url, image=image)
    builtin_url = common.run_plugin_builtin_url(add_save_url)
    context_menu = [(xbmcaddon.Addon().getLocalizedString(33108), builtin_url)]
    return context_menu

@_dir_action
def filters(url):
    di_list = []
    index = 0
    nextAction = 'filters'
    if re.match(r'(.)*id/(2|1[3-6])(.)*.html', url):
        if re.match(r'(.)*id/2.html', url):
            index = 1
        else:
            index = 4
    elif re.match(r'(.)*id/1.html', url):
        index = 2
        if re.match(r'(.)*area/(.)*', url):
            index = 4
    elif re.match(r'(.)*id/3.html', url):
        index = 2
        nextAction = 'shows'
    elif re.match(r'(.)*id/3.html', url):
        index = 2
        nextAction = 'shows'

    if re.match(r'(.)*lang/(.)*', url):
        index = 3
        nextAction = 'shows'

    for all_title, show_url, image in scrapers.types(url, index):
        action_url = common.action_url(nextAction, url=show_url)
        name = all_title
        di_list.append(common.diritem(name, action_url, image))

    if len(di_list) <= 0:
        common.popup(common.getMessage(33305))
        return None

    return di_list

@_dir_action
def shows(url):
    di_list = []
    for all_title, show_url, image in scrapers.shows(url):
        action_url = common.action_url('sources', url=show_url)
        name = all_title
        cm = _saved_to_list_context_menu(all_title, show_url, image)
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))

    if len(di_list) <= 0:
        common.popup(common.getMessage(33305))
        return None

    return di_list

@_dir_action
def sources(url):
    di_list = []
    for name, source_url in scrapers.sources(url):
        action_url = common.action_url('episodes', url=source_url)
        di_list.append(common.diritem(name, action_url))

    if len(di_list) <= 0:
        common.popup(common.getMessage(33305))
        return None

    return di_list

@_dir_action
def recent_updates(url):
    di_list = []
    for name, update_url in scrapers.recent_updates(url):
        action_url = common.action_url('mirrors', url=update_url)
        di_list.append(common.diritem(name, action_url))

    return di_list

@_dir_action
def episodes(url):
    return _episodes(url)

def _episodes(url):
    episodes = scrapers.episodes(url)
    if len(episodes) > 0:
        di_list = []
        for name, episode_url in episodes:
            action_url = common.action_url('play_mirror', url=episode_url)
            epi = cleanstring.episode(name)
            di_list.append(common.diritem(epi, action_url))
        return di_list
    else:
        return []

@_dir_action
def search(url=None):
    if not url:
        heading = xbmcaddon.Addon().getLocalizedString(33301)
        s = common.input(heading)
        s = '%E4%BB%A5%E5%AE%B6%E4%BA%BA'
        if s:
            url = config.search_url % urllib.quote(s.encode('utf8'))
        else:
            return []
    di_list = []
    
    for eng_name, ori_name, show_url, image in scrapers.search(url):
        action_url = common.action_url('episodes', url=show_url)
        name = cleanstring.show(eng_name, ori_name)
        cm = _saved_to_list_context_menu(eng_name, ori_name, show_url, image)
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))
    for page, page_url in scrapers.pages(url):
        action_url = common.action_url('search', url=page_url)
        page_label = cleanstring.page(page)
        di_list.append(common.diritem(page_label, action_url))
    if not di_list:
        common.popup(xbmcaddon.Addon().getLocalizedString(33304))
    return di_list


_saved_list_key = 'saved_list'
def _get_saved_list():
    try:
        return store.get(_saved_list_key)
    except KeyError:
        pass
    try: # backward compatible (try cache)
        return cache.get(_saved_list_key)
    except KeyError:
        return []


@_dir_action
def saved_list():
    sl = _get_saved_list()
    di_list = []
    for all_title, show_url, image in sl:
        action_url = common.action_url('episodes', url=show_url)
        name = all_title
        remove_save_url = common.action_url('remove_saved', all_title=all_title,
                                            show_url=show_url, image=image)
        builtin_url = common.run_plugin_builtin_url(remove_save_url)
        cm = [(xbmcaddon.Addon().getLocalizedString(33109), builtin_url)]
        di_list.append(common.diritem(name, action_url, image, context_menu=cm))
    return di_list

@_action
def add_to_saved(all_title, show_url, image):
    with common.busy_indicator():
        sl = _get_saved_list()
        sl.insert(0, (all_title, show_url, image))
        uniq = set()
        sl = [x for x in sl if not (x in uniq or uniq.add(x))]
        store.put(_saved_list_key, sl)
    common.popup(xbmcaddon.Addon().getLocalizedString(33302))

@_action
def remove_saved(all_title, show_url, image):
    sl = _get_saved_list()
    sl.remove((all_title, show_url, image))
    store.put(_saved_list_key, sl)
    common.refresh()
    common.popup(xbmcaddon.Addon().getLocalizedString(33303))

@_action
def play_mirror(url):
    with common.busy_indicator():
        # soup = BeautifulSoup(common.webread(url), 'html5lib')
        # iframe = soup.find(id='iframeplayer')
        # iframe_url = urljoin(config.base_url, iframe.attrs['src'])
        (vidurl, pars) = scrapers.episodeVideo(urljoin(config.video_url, url)) # common.resolve(url)
        vidurl = _base64(vidurl)
        if not re.match('$\.m3u8', vidurl):
            if re.match('(.*)123ku', pars):
                vidurl = scrapers.episodeVideo_123ku(vidurl)
            else:
                vidurl = scrapers.episodeVideo_dplayer(vidurl)

        if vidurl:
            try:
                title, image = scrapers.title_image(urljoin(config.video_url, url))
            except Exception:
                # we can proceed without the title and image
                title, image = ('', '')

            li = xbmcgui.ListItem(title)
            li.setThumbnailImage(image)
            if 'User-Agent=' not in vidurl:
                vidurl = vidurl + '|User-Agent=' + urllib.quote(get_ua())
            xbmc.Player().play(vidurl, li)

@_dir_action
def mirrors(url):
    return _mirrors(url)

def _mirrors(url):
    mirrors = scrapers.mirrors(url)
    num_mirrors = len(mirrors)
    if num_mirrors > 0:
        di_list = []
        for mirr_label, parts in mirrors:
            for part_label, part_url in parts:
                label = cleanstring.mirror(mirr_label, part_label)
                action_url = common.action_url('play_mirror', url=part_url)
                di_list.append(common.diritem(label, action_url, isfolder=False))
        return di_list
    else:
        # if no mirror listing, try to resolve this page directly
        play_mirror(url)
        return []


def _base64(url64):
    d = 0
    i = ''
    p = 0
    m = 0
    w = 0
    keystr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    url64 = re.sub(r'[^A-Za-z0-9+/=]/g', '', url64)
    url64 = url64[3:]
    while (d < len(url64)):
        b = keystr.index(url64[d])
        d += 1
        if d < len(url64):
            p = keystr.index(url64[d])
        d += 1
        if d < len(url64):
            m = keystr.index(url64[d])
        d += 1
        if d < len(url64):
            w = keystr.index(url64[d])
        d += 1
        o = b << 2 | p >> 4
        c = (15 & p) << 4 | m >> 2
        y = (3 & m) << 6 | w
        i += chr(o)
        if 64 != m:
            i += chr(c)
        if 64 != w:
            i += chr(y)
    return _utf8(i)

def _utf8(e):
    d = ''
    ordi = ''
    ordo = ''
    ordc = ''
    ordy = ''
    b = 0
    while (b < len(e)):
        i = e[b]
        ordi = ord(i)
        if 128 > ordi:
            d += i
        elif 224 > ordi:
            b += 1
            if b < len(e):
                o = e[b]
                ordo = ord(o)
                d += chr((31 & ordi) << 6 | 63 & ordo)
        elif 240 > ordi:
            b += 1
            if b < len(e):
                o = e[b]
            b += 1
            if b < len(e):
                c = e[b]
                ordc = ord(c)
                d += chr((15 & ordi) << 12 | (63 & ordo) << 6 | 63 & ordc)
        else:
            b += 1
            if b < len(e):
                o = e[b]
                ordo = ord(o)
            b += 1
            if b < len(e):
                c = e[b]
                ordc = ord(c)
            b += 1
            if b < len(e):
                y = e[b]
                ordy = ord(y)
                d += chr((7 & ordi) << 18 | (63 & ordo) << 12 | (63 & ordc) << 6 | 63 & ordo)

        b += 1

    return d
