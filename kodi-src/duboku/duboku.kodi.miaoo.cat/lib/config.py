import os.path
from urlparse import urljoin
from lib.common import diritem, action_url, profile_dir

base_url = 'https://www.duboku.tv'
video_url = 'https://tv.gboku.com'
cache_file = os.path.join(profile_dir, 'cache.pickle')
store_file = os.path.join(profile_dir, 'store.pickle')

# the trailing forward slashes are necessary
# without it, page urls will be wrong (icdrama bug)
search_url = urljoin(base_url, '/vodsearch/-------------.html?wd=%s&submit=')
index_items = [
    diritem(33000, action_url('saved_list')),
    diritem(33005, action_url('shows', url=urljoin(base_url, '/vodshow/20-----------.html'))),
    diritem(33001, action_url('filters', url=urljoin(base_url, '/vodshow/2-----------.html'))),
    diritem(33002, action_url('filters', url=urljoin(base_url, '/vodshow/1-----------.html'))),
    diritem(33003, action_url('filters', url=urljoin(base_url, '/vodshow/3-----------.html'))),
    diritem(33004, action_url('shows', url=urljoin(base_url, '/vodshow/4-----------.html'))),
    # diritem(33006, action_url('search'))
]
