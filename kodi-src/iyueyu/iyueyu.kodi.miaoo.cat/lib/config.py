import os.path
from urlparse import urljoin
from lib.common import diritem, action_url, profile_dir

base_url = 'https://www.iyueyuz.com'
video_url = 'https://www.iyueyuz.com'
cache_file = os.path.join(profile_dir, 'cache.pickle')
store_file = os.path.join(profile_dir, 'store.pickle')

# the trailing forward slashes are necessary
# without it, page urls will be wrong (icdrama bug)
search_url = urljoin(base_url, '/vodsearch/-------------.html?wd=%s&submit=')
index_items = [
    diritem(33000, action_url('saved_list')),
    diritem(33005, action_url('shows', url=urljoin(base_url, '/index.php%2Fvod%2Fshow%2Fid%2F14%2Flang%2F%E7%B2%A4%E8%AF%AD.html'))),
    diritem(33001, action_url('filters', url=urljoin(base_url, '/index.php/vod/show/id/2.html'))),
    diritem(33002, action_url('filters', url=urljoin(base_url, '/index.php/vod/show/id/1.html'))),
    diritem(33003, action_url('filters', url=urljoin(base_url, '/index.php/vod/show/id/3.html'))),
    diritem(33004, action_url('filters', url=urljoin(base_url, '/index.php/vod/show/id/4.html'))),
    # diritem(33006, action_url('search'))
]
