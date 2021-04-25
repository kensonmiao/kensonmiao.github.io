import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from contextlib import contextmanager
from os.path import abspath, dirname
from urllib.parse import urlencode, quote
from resolveurl.hmf import HostedMediaFile
import resolveurl
from resolveurl.lib.net import Net, get_ua, HttpResponse
import urllib.request
#import requests

_plugin_url = sys.argv[0]
_handle = int(sys.argv[1])
_dialog = xbmcgui.Dialog()

profile_dir = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

def debug(s):
    xbmc.log(str(s), xbmc.LOGDEBUG)

def error(s):
    xbmc.log(msg=str(s), level=xbmc.LOGERROR)

def webread(url):
    req = urllib.request.Request(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; SM-N976N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.143 Mobile Safari/537.36 MicroMessengeriptv/1.2.6 VideoPlayer god/3.0.0 MPC 2.4.23 mitv baiduboxapp Edge/14.14393 Html5Plus/1.0 (Immersed/24.0)',
        'X-Requested-With': 'w2a.app.iptv800.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': 'UM_distinctid=178df6ca0c4b-02e35691701d5b-2579436c-57e40-178df6ca0c5ba; _ga=GA1.2.1023821354.1618656142; _gid=GA1.2.160775913.1618656142; appid=__W2A__app.iptv800.com; CNZZDATA1273922221=1108430403-1618653332-%7C1618696572; iptvad=1; _gat_gtag_UA_120439249_1=1; idss=2000'
    }
    for key in headers:
        req.add_header(key, headers[key])
    resp = urllib.request.urlopen(req, timeout=15)
    netResp = HttpResponse(resp)
    return netResp.content

def action_url(action, **action_args):
    action_args['action'] = action
    for k, v in action_args.items():
        action_args[k] = v.encode('utf8')
    qs = urlencode(action_args)
    return _plugin_url + '?' + qs

def add_item(diritem):
    xbmcplugin.addDirectoryItem(**diritem)

def end_dir():
    xbmcplugin.endOfDirectory(_handle)

def diritem(label_or_stringid, url, image='', isfolder=True, context_menu=[], info=None):
    if type(label_or_stringid) is int:
        label = xbmcaddon.Addon().getLocalizedString(label_or_stringid)
    else:
        label = label_or_stringid
    listitem = xbmcgui.ListItem(label)
    listitem.setArt({ 'thumb': image, 'icon': image })
    listitem.setInfo('video', { 
        'plot': info
     })
    listitem.addContextMenuItems(context_menu, replaceItems=True)
    # this is unpackable for xbmcplugin.addDirectoryItem
    return dict(
        handle   = _handle,
        url      = url,
        listitem = listitem,
        isFolder = isfolder
    )

def getMessage(label_or_stringid):
    if type(label_or_stringid) is int:
        return xbmcaddon.Addon().getLocalizedString(label_or_stringid)
    else:
        return label_or_stringid

def popup(s):
    addon_name = xbmcaddon.Addon().getAddonInfo('name')
    try:
        # Gotham (13.0) and later
        _dialog.notification(addon_name, s)
    except AttributeError:
        _dialog.ok(addon_name, s)

def select(heading, options):
    return _dialog.select(heading, options)

def resolve(url):
    url = url.encode('utf8')
    url = quote(url, ':/')

    # import the resolvers so that resolveurls pick them up
    import lib.resolvers
    hmf = HostedMediaFile(url)
    if hmf:
        return hmf.resolve()
    else:
        return ""

def sleep(ms):
    xbmc.sleep(ms)

def back_dir():
    # back one directory
    xbmc.executebuiltin('Action(ParentDir)')

def refresh():
    # refresh directory
    xbmc.executebuiltin('Container.Refresh')

def run_plugin(url):
    xbmc.executebuiltin(run_plugin_builtin_url(url))

def run_plugin_builtin_url(url):
    return 'RunPlugin(%s)' % url

def input(heading):
    kb = xbmc.Keyboard(default='', heading=heading)
    kb.doModal()
    if kb.isConfirmed():
        return kb.getText()
    return None

@contextmanager
def busy_indicator():
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialog)')
