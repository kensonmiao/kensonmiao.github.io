import re
import urllib
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from lib import cache, config, common
import base64
import js2py

def _get(url):
    # only scrape within the site
    return common.webread(url)

def _soup(url):
    soup = BeautifulSoup(_get(url), 'html5lib')
    return soup

def getTVSources(url):
    soup = _soup(url)
    show_list = []
    for t in soup.select('ul[data-role="listview"] a'):
        all_title = t.getText()
        show_url = t['onclick'].replace('clicked(\'', '').replace('\');', '')
        show_list.append((all_title, '/iptv.php' + show_url, '')) 
    
    return show_list

def categories(url):
    soup = _soup(url)
    token = None
    for tag in soup.find_all('script'):
        if 'bdecodeb' in tag.getText():
            token = __decode(tag.getText())
            break
        
    show_list = []
    common.error(token)
    if hasattr(token, 'token'):
        options = soup.select('#playURL > option')
        for t in options:
            all_title = t.getText()
            show_url = t['value']
            common.error(show_url)
            show_url = __decodeUrl(show_url, token.hken, token.token)
            common.error(show_url)
            show_list.append((all_title, show_url, '')) 
    else:
        titleTile = soup.find('title')
        show_list.append((titleTile.getText(), token, '')) 

    return show_list

def __decode(js):
    docJs = """
        function unbox() { 
            var evalCode = ""; 
            var document = { 
                write: function(str) { evalCode = str; } 
            }; 
            var bdecodeb = function(str, key) { return {str: str, key: key}; }; """ + js + """ return evalCode; }"""
    strAndKey = js2py.eval_js(docJs)()
    decodedStr = __bdecodeb(strAndKey.str, strAndKey.key)
    decodedStr = BeautifulSoup(decodedStr, 'html5lib').get_text()
    if "token" in decodedStr:
        test = js2py.eval_js('function add() { ' + decodedStr + '; return { token: token, hken: hken}; }')
        tokenObj = test()
        return tokenObj
    else:
        presetCode = """
            function secondUnbox() {
                var plus = { video: { VideoPlayer: function(str, code) { return code; } } };
                var document = { addEventListener: function(event, func) {} };
                """ + __bdecode_str() + ";" + decodedStr + """
                vstPlay();
                return video.src;
            }
        """
        common.error(presetCode)
        src = js2py.eval_js(presetCode)()
        return src

def __decodeUrl(cryptedUrl, hken, token):
    try:
        url = cryptedUrl[::-1]
        url = __bdecodeb(url, hken)
        url = url.replace('token=123', 'token=' + token)
        url = url.replace(hken, '')
        if url not in (None, ''):
            return url
    except:
        return None

def __bdecodeb(str,key):
    bdecodeb = js2py.eval_js(__bdecodeb_str())
    decryptedStr = bdecodeb(str, key)
    return decryptedStr

def __bdecodeb_str():
    return """
        function bdecodeb(str,key) {
            """ + __bdecode_str() + """
            string = bdecode(str);
            len = key.length;
            code = "";
            for (i = 0; i < string.length; i++) {
                k = i % len;
                code += String.fromCharCode(string.charCodeAt(i) ^ key.charCodeAt(k));
            }
            stra = bdecode(code);
            return stra;
        }
    """

def __bdecode_str():
    return """
        var bdecode = function(data) {
            var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
            var a1, a2, a3, h1, h2, h3, h4, bits, i = 0,
            ac = 0,
            dec = "",
            tmp_arr = [];
            if (!data) {
                return data;
            }
            data += '';
            do {
                h1 = keyStr.indexOf(data.charAt(i++));
                h2 = keyStr.indexOf(data.charAt(i++));
                h3 = keyStr.indexOf(data.charAt(i++));
                h4 = keyStr.indexOf(data.charAt(i++));
                bits = h1 << 18 | h2 << 12 | h3 << 6 | h4;
                a1 = bits >> 16 & 0xff;
                a2 = bits >> 8 & 0xff;
                a3 = bits & 0xff;
                if (h3 == 64) {
                    tmp_arr[ac++] = String.fromCharCode(a1);
                } else if (h4 == 64) {
                    tmp_arr[ac++] = String.fromCharCode(a1, a2);
                } else {
                    tmp_arr[ac++] = String.fromCharCode(a1, a2, a3);
                }
            } while (i < data.length);
            dec = tmp_arr.join('');
            return dec;
        }
    """

@cache.memoize(10)
def types(url, index):
    soup = _soup(url)
    tag = soup.select("div.myui-panel_bd > div.slideDown-box > ul")
    li = tag[index].select('a')
    type_list = []
    for alink in li:
        if "text-muted" not in alink["class"] and "btn-warm" not in alink["class"]:
            all_title = alink.getText()
            show_url = urljoin(config.base_url, alink['href'])
            type_list.append((all_title, show_url, '')) 
    return type_list

@cache.memoize(10)
def shows(url):
    soup = _soup(url)
    imgs = soup.select("div.myui-panel.myui-panel-bg img")
    for img in imgs:
        if img['src'] == '/template/mytheme/statics/img/no.png':
            return []
    tiles = soup.find_all('a', attrs={'data-original' : True})
    show_list = []
    for t in tiles:
        all_title = t['title']
        show_url = urljoin(config.base_url, t['href'])
        image = t.get('data-original')
        show_list.append((all_title, show_url, image)) 
    return show_list

def search(url):
    soup = _soup(url)
    tiles = soup.select("ul.myui-vodlist__media li.clearfix")
    show_list = []
    for t in tiles:
        alink = t.select("a[data-original]")[0]
        all_title = alink['title']
        show_url = urljoin(config.base_url, alink['href'])
        image = alink['data-original']

        detail = t.select('div.detail')[0].findChildren("p" , recursive=False)
        info = ''
        for p in detail:
            pstr = re.sub('\<a (.*?)\<\/a\>', '', str(p))
            pstr = pstr.replace('<span class="split-line"></span>', ' ')
            info += BeautifulSoup(pstr, 'html5lib').getText() + ' '

        show_list.append((all_title, show_url, image, info)) 
    return show_list

@cache.memoize(10)
def pages(url):
    soup = _soup(url)
    page_list = soup.select('ul.myui-page > li > a')
    return [(p.getText(), urljoin(url, p['href'])) for p in page_list if 'href' in p.attrs]

@cache.memoize(10)
def recent_updates(url):
    soup = _soup(url)
    updates = soup.select('ul.listep > li > a')
    return [(u.getText(), urljoin(url, u['href'])) for u in updates]

@cache.memoize(10)
def episodes(url):
    soup = _soup(url)
    butts = [b for b in reversed(soup.select('ul.myui-content__list > li > a'))]
    return [(b.getText(), b['href']) for b in butts]

@cache.memoize(10)
def episodeVideo(url):
    soup = _soup(url)
    for tag in soup.find_all('script'):
        if tag.getText().find('player_data=') >= 0:
            url = re.search(r'https:(.[^,])*\.m3u8', tag.getText()).group()
            url = url.replace('\/', '/')
            return url
    
    return None

@cache.memoize(10)
def mirrors(url):
    soup = _soup(url)
    mirrs = [node.getText() for node in soup.select('span.tite')]
    mirr_parts = [node.find_all('a', recursive=False)
                  for node in soup.select('ul.tn-uldef')]
    mirr_list = []
    for mirr, parts in zip(mirrs, mirr_parts):
        parts = [(p.getText(), p['href']) for p in parts]
        mirr_list.append((mirr, parts))
    return mirr_list

@cache.memoize(60)
def title_image(mirror_url):
    soup = _soup(mirror_url)
    title = soup.find('title').getText()
    image = ''
    return (title, image)

def category_page(url):
    # Note: use the url itself to get category name and page
    relpath = urlparse(url).path.lstrip('/')
    m = re.search(r'^[A-Za-z-]+', relpath)
    category = m.group(0).replace('-', ' ').capitalize() if m else 'Unknown'
    m = re.search(r'page-(\d+)\.html', relpath)
    page = m.group(1) if m else '1'
    return (category, page)

def search_page(url):
    # Note: use the url itself to get search text and page
    relpath = urlparse(url).path.lstrip('/')
    m = re.search(r'search/([%1-9A-Za-z_\.-]+)', relpath)
    text = urllib.unquote(m.group(1)) if m else ''
    m = re.search(r'page-(\d+)\.html', relpath)
    page = m.group(1) if m else '1'
    return (text, page)

def show_name(url):
    # same template as title_image
    title, _ = title_image(url)
    return title

def version_name(url):
    # same template as title_image
    title, _ = title_image(url)
    return title
