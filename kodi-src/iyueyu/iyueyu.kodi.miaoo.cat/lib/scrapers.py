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
    tag = soup.select("div.fed-casc-list.fed-part-rows > dl")
    li = tag[index].select('a')
    type_list = []
    for alink in li:
        if 'class' not in alink.attrs or "fed-this" not in alink["class"]:
            all_title = alink.getText()
            show_url = urljoin(config.base_url, alink['href'])
            type_list.append((all_title, show_url, '')) 
    return type_list

@cache.memoize(10)
def shows(url):
    soup = _soup(url)
    tiles = soup.select('ul.fed-list-info.fed-part-rows > li')
    show_list = []
    for t in tiles:
        aLink = t.find_all('a')[1]
        all_title = aLink.getText()
        show_url = urljoin(config.base_url, aLink['href'])
        image = t.find_all('a', attrs={'data-original' : True})[0].get('data-original')
        show_list.append((all_title, show_url, image)) 
    return show_list

@cache.memoize(10)
def sources(url):
    soup = _soup(url)
    ul = soup.select("div.fed-tabs-boxs ul.fed-part-rows")
    tag = ul[0].select('a')
    return [(b.getText(), urljoin(config.base_url, b['href'])) for b in tag]

def search(url):
    # same template as shows
    return shows(url)

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
    ul = soup.select("div.fed-tabs-boxs ul.fed-part-rows")
    tag = ul[2].select('a')
    return [(b.getText(), urljoin(config.base_url, b['href'])) for b in reversed(tag)]

@cache.memoize(10)
def episodeVideo(url):
    soup = _soup(url)
    tag = soup.find("iframe", attrs={'data-play' : True})
    return (tag['data-play'], tag['data-pars'])

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
