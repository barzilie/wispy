import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.dns_filters import is_ad_tracking_domain


def test_blocks_common_ad_hosts():
    assert is_ad_tracking_domain('googleads.g.doubleclick.net')
    assert is_ad_tracking_domain('pagead2.googlesyndication.com')
    assert is_ad_tracking_domain('ads.pubmatic.com')


def test_allows_normal_hosts():
    assert not is_ad_tracking_domain('api.spotify.com')
    assert not is_ad_tracking_domain('www.wikipedia.org')
    assert not is_ad_tracking_domain('')


if __name__ == '__main__':
    test_blocks_common_ad_hosts()
    test_allows_normal_hosts()
    print('dns filter tests ok')
