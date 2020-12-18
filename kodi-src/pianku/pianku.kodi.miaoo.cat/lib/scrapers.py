import re
import urllib
from urlparse import urljoin, urlparse
from bs4 import BeautifulSoup
from lib import cache, config, common

@cache.memoize()
def _get(url):
    # only scrape within the site
    return common.webread(url)

@cache.memoize()
def _soup(url):
    soup = BeautifulSoup(_get(url), 'html5lib')
    return soup

@cache.memoize(10)
def types(url, index):
    soup = _soup(url)
    type_list = []
    p = re.compile(r'-')
    index_list = []
    for m in p.finditer(url):
        index_list.append(m.start())
    for tag in soup.select('dl[class="' + index + '"] dd[data-a]'):
        if tag['data-a'] != '0':
            paramIndex = int(tag['data-b'])
            newlink = url[:index_list[paramIndex]] + tag['data-a'] + url[index_list[paramIndex]:]
            type_list.append((tag.getText(), newlink))

    return type_list

@cache.memoize(10)
def shows(url):
    soup = _soup(url)
    tiles = soup.select('ul.content-list div.li-img a')
    show_list = []
    for t in tiles:
        all_title = t['title']
        show_url = urljoin(config.base_url, t['href'])
        image = t.find('img', {'data-funlazy': True})['data-funlazy']
        show_list.append((all_title, show_url, image)) 
    return show_list

@cache.memoize(10)
def sources(url):
    id_match = re.search(r'https://(.*)/(.*)/(.*)\.html', url)
    id = id_match.group(3)
    soup = _soup(url)
    newUrl = ''
    for tag in soup.select('script'):
        match = re.search(r"\$\(('|\")\#url('|\")\)\.load\(('|\")(.*)('|\")\)", str(tag))
        if match:
            newUrl = urljoin(config.base_url, re.sub(r'(\'|")(.*)id(.*)(\'|")', id, match.group(4)))
            break

    soup = _soup(newUrl)
    lis = soup.select('#play ul.py-tabs li')
    return [(tag.getText(), newUrl + '?tab=' + str(lis.index(tag)) + '&prevUrl=' + url) for tag in lis]

def search(url):
    soup = _soup(url)
    tiles = soup.select("main dl")
    show_list = []
    for t in tiles:
        imgTile = t.select("dt a img['data-funlazy']")[0]
        alink = t.select("dd p")[0].select('strong a')[0]
        all_title = alink.getText()
        show_url = urljoin(config.base_url, alink['href'])
        image = imgTile['data-funlazy']

        detail = t.select('dd')[0].findChildren("p" , recursive=False)
        indexList = [0,2,3,4]
        if len(detail) == 4:
            indexList = [0,1,2,3] 
        info = ''
        try:
            info = detail[indexList[0]].select('span.ss1')[0].getText()
        except:
            pass
        try:
            info += (' ' + detail[indexList[1]].getText())
        except:
            pass
        try:
            cast = detail[indexList[2]].getText()
            if len(cast) > 20:
                info += (' ' + cast[:20] + '...')
            else:
                info += (' ' + cast)
        except:
            pass
        try:
            info +=  (' ' + detail[indexList[3]].getText())
        except:
            pass

        show_list.append((all_title, show_url, image, info))
    
    return show_list

@cache.memoize(10)
def pages(url):
    soup = _soup(url)
    page_list = soup.select('div.pages a')
    return [(p.getText(), urljoin(url, p['href'])) for p in page_list if 'href' in p.attrs]

@cache.memoize(10)
def recent_updates(url):
    soup = _soup(url)
    updates = soup.select('ul.listep > li > a')
    return [(u.getText(), urljoin(url, u['href'])) for u in updates]

@cache.memoize(10)
def episodes(url):
    indexQM = url.index('?')
    origUrl = url[:indexQM]
    params = url[indexQM:].split('&')
    tab_match = re.search(r'([0-9]*)$', params[0])
    tabIndex = int(tab_match.group(0))
    soup = _soup(params[1].replace('prevUrl=', ''))
    soup = _soup(origUrl)
    ul = soup.select("div.bd > ul.player")
    tag = ul[tabIndex].select('a')
    return [(b.getText(), urljoin(config.base_url, b['href'])) for b in reversed(tag)]

@cache.memoize(10)
def episodeVideo(url):
    soup = _soup(url)
    title = soup.find('title').getText()
    scripts = soup.select("script")
    for s in scripts:
        matched = re.search(r'geturl\((\'|")(.*)(\'|")\)', str(s))
        if matched:
            return (title, matched.group(2))

@cache.memoize(10)
def episodeVideo_dplayer(url):
    soup = _soup(url)
    tags = soup.find_all("script")
    for t in tags:
        matched = re.search(r'\"url\"\:\"(.*)\.m3u8', str(t))
        if matched:
            host = re.search(r'redirecturl(.*)\"(.*)\"', str(t))
            return host.group(2) + matched.group(1) + '.m3u8'

@cache.memoize(10)
def episodeVideo_123ku(url):
    soup = _soup(url)
    tags = soup.find_all("script")
    for t in tags:
        matched = re.search(r'url(.*)(\'|\")(.*)\.m3u8', str(t))
        if matched:
            return matched.group(3) + '.m3u8'

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
    data = soup.find('div', attrs={'data-name' : True, 'data-nums' : True})
    if data:
        return (data['data-name'] + ' ' + data['data-nums'], '')
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
