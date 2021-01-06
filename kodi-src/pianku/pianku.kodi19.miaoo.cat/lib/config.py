import os.path
from urllib.parse import urljoin
from lib.common import diritem, action_url, profile_dir

base_url = 'https://www.pianku.me'
cache_file = os.path.join(profile_dir, 'cache.pickle')
store_file = os.path.join(profile_dir, 'store.pickle')
local_proxy = 'http://localhost:11133'
domain_using_proxy = ['mahua-kb\.com', 'okzy\.com', 'kuyun\.com']


# the trailing forward slashes are necessary
# without it, page urls will be wrong (icdrama bug)
search_url = urljoin(base_url, '/s/%s.html')
index_items = [
    diritem(33000, action_url('saved_list')),
    diritem(33005, action_url('shows', url=urljoin(base_url, '/tv/--_E9_A6_99_E6_B8_AF----1.html'))),
    diritem(33001, action_url('filters', url=urljoin(base_url, '/tv/------1.html'))),
    diritem(33002, action_url('filters', url=urljoin(base_url, '/mv/------1.html'))),
    diritem(33004, action_url('filters', url=urljoin(base_url, '/ac/------1.html'))),
    diritem(33006, action_url('search'))
]
