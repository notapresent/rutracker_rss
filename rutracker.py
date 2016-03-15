# Parser
from lxml import etree, cssselect
from ttscraper import parsers, webclient
from ttscraper.debug import debug_dump
from ttscraper import dao


class Parser(parsers.BaseParser):
    def parse_index(self, html):
        rows = self.parse_index_table(html)
        return [self.parse_index_row(row) for row in rows]

    def parse_torrent_page(self, html):
        tree = parsers.make_tree(html)
        try:
            rv = {
                'categories': self.torrent_categories(tree),
                'description': self.torrent_description(tree),
                'btih': self.torrent_btih(tree)
            }
        except IndexError as e:
            debug_dump('/debug/parser/index_error', html)
            raise parsers.Error(str(e))

        return rv

    def parse_index_table(self, html):
        tree = parsers.make_tree(html)
        """Returns list of index rows represented as etree.Elements"""
        rows_selector = cssselect.CSSSelector('table#tor-tbl tr.tCenter.hl-tr')
        return rows_selector(tree)

    def parse_index_row(self, row):
        """Parse index row represented by lxml element and return dict"""
        tid = self.index_tid(row)
        title = self.index_title(row)
        ts = self.index_timestamp(row)
        nbytes = self.index_nbytes(row)

        return {
            'tid': tid,
            'title': title,
            'timestamp': ts,
            'nbytes': nbytes
            }

    def index_tid(self, elem):
        title_link_selector = cssselect.CSSSelector('td.t-title div.t-title a')
        a = title_link_selector(elem)[0]
        tid = a.attrib['data-topic_id']
        return int(tid)

    def index_title(self, elem):
        title_link_selector = cssselect.CSSSelector('td.t-title div.t-title a')
        a = title_link_selector(elem)[0]
        return a.text

    def index_timestamp(self, elem):
        timestamp_selector = cssselect.CSSSelector('td:last-child u')
        timestamp = timestamp_selector(elem)[0].text
        return int(timestamp)

    def index_nbytes(self, elem):
        nbytes_selector = cssselect.CSSSelector('td.tor-size u')
        nbytes = nbytes_selector(elem)[0].text
        return int(nbytes)

    def torrent_categories(self, tree):
        cat_selector = cssselect.CSSSelector('td.nav.w100.pad_2.brand-bg-white > span > a')
        cat_links = cat_selector(tree)
        return [self.parse_category_link(elem) for elem in cat_links]

    def parse_category_link(self, link):
        """Parse category link and return tuple (id, kind, title).

        Kind is one of r, c, f for root, category and forum"""
        href = link.attrib['href']
        if '=' in href:
            head, tail = href.split('=')
            cat_id = int(tail)
            cat_kind = head[-1]
        else:
            cat_id = 0
            cat_kind = 'r'

        return (cat_id, cat_kind, link.text)

    def torrent_description(self, tree):
        desc_selector = cssselect.CSSSelector('div.post_body')
        elem = desc_selector(tree)[0]
        contents_list = [etree.tostring(e, encoding='utf-8') for e in elem.iterchildren()]
        return ''.join(contents_list)

    def torrent_btih(self, tree):
        btih_selector = cssselect.CSSSelector('.attach_link.guest > a')
        elem = btih_selector(tree)[0]

        return parsers.btih_from_href(elem.attrib['href'])


class WebClient(webclient.BaseWebClient):
    """Tracker-specific adapter"""
    TORRENT_PAGE_URL = 'http://rutracker.org/forum/viewtopic.php?t={}'
    LOGIN_URL = 'http://login.rutracker.org/forum/login.php'
    INDEX_URL = 'http://rutracker.org/forum/tracker.php'
    INDEX_FORM_DATA = {'prev_new': 0, 'prev_oop': 0, 'f[]': -1, 'o': 1, 's': 2, 'tm': -1, 'oop': 1}
    ENCODING = 'windows-1251'
    USER_MARKER = ('<a class="logged-in-as-uname" '
                   'href="http://rutracker.org/forum/profile.php?mode=viewprofile&amp;u={}">')

    def get_torrent_page(self, tid):
        """"Returns torrent page content"""
        url = self.TORRENT_PAGE_URL.format(tid)
        resp = self.request(url)
        return self.get_text(resp)

    def get_index_page(self):
        """Returns page with latest torrents list"""
        with dao.account_context() as account:
            resp = self.user_request(account, self.INDEX_URL, method='POST', data=self.INDEX_FORM_DATA)
        return self.get_text(resp)

    def tracker_log_in(self, account):
        """Log in user via tracker log in form, returns True if login succeeded"""
        formdata = WebClient.login_form_data(account)

        resp = self.request(self.LOGIN_URL, method='POST', data=formdata)
        html = self.get_text(resp)

        if html and not WebClient.is_logged_in(html, account):
            raise LoginFailed("Server login failed for {} ".format(account))

    @classmethod
    def is_logged_in(cls, html, account):
        """Check if the page was requested with user logged in"""
        marker = cls.USER_MARKER.format(account.userid)
        return marker in html

    @classmethod
    def login_form_data(cls, account):
        return {
            'login_password': account.password,
            'login_username': account.username,
            'login': 'Whatever'        # Must be non-empty
        }

