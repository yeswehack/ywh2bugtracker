import unittest

from ywh2bt.core.html import (
    cleanup_ywh_redirects_from_html,
    cleanup_ywh_redirects_from_text,
)


class TestHtml(unittest.TestCase):

    def test_cleanup_ywh_redirects_from_html(self) -> None:
        html = '''
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F&amp;expires=1620659652&amp;token=1062673b9672f13bd9579de55735466c241828e9dbce8dcd350050c28410f2fe">
    https://example.com/
</a>
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ffoo%253Dbar&amp;expires=1620659652&amp;token=17ea19649d6c141b3cb6875d7f2104f6d52956729573d1686da7f951a951c359">
    https://example.com/?foo=bar
</a>
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ftoken%253D123&amp;expires=1620659652&amp;token=e75cba14b6f16d3d427985f0d6505529fd5f94feb9ae5058527cda10335b48c4">
    https://example.com/?token=123
</a>
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Fexpires%253D456&amp;expires=1620659652&amp;token=b2b1d09d93ade1d966811c90c9fe61dac31f4d7347b001a93ff41a9492edd144">
    https://example.com/?expires=456
</a>
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ftoken%253D123%2526expires%253D456&amp;expires=1620659652&amp;token=79fc255c26edc84e2e750c8428bd09b045ffdcd381f76113a09a8390b0af3a34">
    https://example.com/?token=123&amp;expires=456
</a>
<a href="https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ffoo%253Dbar%2526token%253D123%2526expires%253D456&amp;expires=1620659652&amp;token=e2beb06927675cf3bc69d15a91e64d49278e987e23d9d31e9edea83d5e599e41">
    https://example.com/?foo=bar&amp;token=123&amp;expires=456
</a>'''
        cleaned = cleanup_ywh_redirects_from_html(
            ywh_domain='ywh.domain',
            html=html,
        )
        self.assertEqual(
            '''
<a href="https://example.com/">
    https://example.com/
</a>
<a href="https://example.com/?foo=bar">
    https://example.com/?foo=bar
</a>
<a href="https://example.com/?token=123">
    https://example.com/?token=123
</a>
<a href="https://example.com/?expires=456">
    https://example.com/?expires=456
</a>
<a href="https://example.com/?token=123&amp;expires=456">
    https://example.com/?token=123&amp;expires=456
</a>
<a href="https://example.com/?foo=bar&amp;token=123&amp;expires=456">
    https://example.com/?foo=bar&amp;token=123&amp;expires=456
</a>''',
            cleaned,
        )

    def test_cleanup_ywh_redirects_from_text(self) -> None:
        text = '''
[https://example.com/](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F&expires=1620659652&token=1062673b9672f13bd9579de55735466c241828e9dbce8dcd350050c28410f2fe)
[https://example.com/?foo=bar](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ffoo%253Dbar&expires=1620659652&token=17ea19649d6c141b3cb6875d7f2104f6d52956729573d1686da7f951a951c359)
[https://example.com/?token=123](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ftoken%253D123&expires=1620659652&token=e75cba14b6f16d3d427985f0d6505529fd5f94feb9ae5058527cda10335b48c4)
[https://example.com/?expires=456](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Fexpires%253D456&expires=1620659652&token=b2b1d09d93ade1d966811c90c9fe61dac31f4d7347b001a93ff41a9492edd144)
[https://example.com/?token=123&expires=456](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ftoken%253D123%2526expires%253D456&expires=1620659652&token=79fc255c26edc84e2e750c8428bd09b045ffdcd381f76113a09a8390b0af3a34)
[https://example.com/?foo=bar&token=123&expires=456](https://ywh.domain/redirect?url=https%253A%252F%252Fexample.com%252F%253Ffoo%253Dbar%2526token%253D123%2526expires%253D456&expires=1620659652&token=e2beb06927675cf3bc69d15a91e64d49278e987e23d9d31e9edea83d5e599e41)'''
        cleaned = cleanup_ywh_redirects_from_text(
            ywh_domain='ywh.domain',
            text=text,
        )
        self.assertEqual(
            cleaned,
            '''
[https://example.com/](https://example.com/)
[https://example.com/?foo=bar](https://example.com/?foo=bar)
[https://example.com/?token=123](https://example.com/?token=123)
[https://example.com/?expires=456](https://example.com/?expires=456)
[https://example.com/?token=123&expires=456](https://example.com/?token=123&expires=456)
[https://example.com/?foo=bar&token=123&expires=456](https://example.com/?foo=bar&token=123&expires=456)''',
        )
