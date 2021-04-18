import xbmc
import xbmcgui
import urllib
import functools
import xbmcaddon
import re
import urllib.parse as urlparse
from urllib.parse import quote, urljoin, quote_plus, unquote, parse_qs
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
    di_list = []
    
    url = urljoin(config.base_url, '/iptv.php?tid=gt')
    for tv_title, tv_url, image in scrapers.getTVSources(url):
        action_url = common.action_url('mirrors', url=urljoin(config.base_url,tv_url), title=tv_title)
        di_list.append(common.diritem(tv_title, action_url, image))

    return di_list
    

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
    if re.match(r'(.)*2-----------\.html', url):
        nextAction = 'shows'
    elif re.match(r'(.)*1-(.)*----------\.html', url):
        index = 1
        if re.match(r'(.)*1-(.)+----------\.html', url):
            index = 2
            nextAction = 'shows'
    elif re.match(r'(.)*3-----------\.html', url):
        index = 1
        nextAction = 'shows'
    else:
        return shows(url)

    action_url = common.action_url('shows', url=url)
    di_list.append(common.diritem(common.getMessage(33007), action_url, ''))
    for all_title, show_url, image in scrapers.types(url, index):
        action_url = common.action_url(nextAction, url=show_url)
        name = all_title
        di_list.append(common.diritem(name, action_url, image))
    return di_list

@_dir_action
def shows(url):
    return []

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
        if s:
            url = config.search_url % quote_plus(s)
        else:
            return []

    di_list = []
    
    for ori_name, show_url, image, info in scrapers.search(url):
        action_url = common.action_url('episodes', url=show_url)
        cm = _saved_to_list_context_menu(ori_name, show_url, image)
        di_list.append(common.diritem(ori_name, action_url, image, context_menu=cm, info=info))

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
def play_mirror(url, title):
    with common.busy_indicator():
        # soup = BeautifulSoup(common.webread(url), 'html5lib')
        # iframe = soup.find(id='iframeplayer')
        # iframe_url = urljoin(config.base_url, iframe.attrs['src'])
        vidurl = quote(url, ':/?&=') # common.resolve(url)

        if vidurl:
            li = xbmcgui.ListItem(title)
            xbmc.Player().play(vidurl, li)

@_dir_action
def mirrors(url, title):
    return _mirrors(url, title)

def _mirrors(url, title):
    di_list = []
    for all_title, show_url, image in scrapers.categories(url):
        action_url = common.action_url('play_mirror', url=show_url, title=title + '-' + all_title)
        name = all_title
        di_list.append(common.diritem(name, action_url, image))
    return di_list
