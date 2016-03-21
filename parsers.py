# coding: utf-8
"""Everythong related to parsing tracker responses"""
import urlparse
from lxml import etree, cssselect

from debug import debug_dump


class Parser(object):
    def parse_index(self, html):
        rows = self.parse_index_table(html)
        return [self.parse_index_row(row) for row in rows]

    def parse_torrent_page(self, html):
        tree = make_tree(html)
        validate_torrent(tree)

        try:
            categories = self.torrent_categories(tree)
            description = self.torrent_description(tree)
            btih = self.torrent_btih(tree)

        except IndexError as e:
            debug_dump('/debug/parser_torrent_error', html)
            raise Error(str(e))

        torrent_data = {
            'description': description,
            'btih': btih
        }

        return (torrent_data, categories)

    def parse_index_table(self, html):
        tree = make_tree(html)
        """Returns list of index rows represented as etree.Elements"""
        rows_selector = cssselect.CSSSelector('table#tor-tbl tr.tCenter.hl-tr')
        return rows_selector(tree)

    def parse_index_row(self, row):
        """Parse index row represented by lxml element and return dict"""
        try:
            tid = self.index_tid(row)
            title = self.index_title(row)
            ts = self.index_timestamp(row)
            nbytes = self.index_nbytes(row)

        except IndexError as e:
            debug_dump('/debug/parser_index_row_error', etree.tostring(row))
            raise Error(str(e))

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
        btih_link_selector = cssselect.CSSSelector('a.med.magnet-link-16')
        elem = btih_link_selector(tree)[0]

        return btih_from_href(elem.attrib['href'])


def btih_from_href(url):
    """Extracts infohash from magnet link"""
    parsed = urlparse.urlparse(url)
    params = urlparse.parse_qs(parsed.query)
    xt = params['xt'][0]
    return xt[9:]


def make_tree(html):
    """Make lxml.etree from html"""
    htmlparser = etree.HTMLParser(encoding='utf-8')
    return etree.fromstring(html, parser=htmlparser)


def validate_torrent(tree):
    """Checks torrent page for signs of removed/unapproved torrent

    Raises SkipTorrent if torrent is not valid"""
    check_topic_deleted(tree)
    check_torrent_status(tree)


def check_topic_deleted(tree):
    """Checks if torrent was deleted"""
    sel = cssselect.CSSSelector('table.message tr > td > div.mrg_16')
    block = sel(tree)
    if block and block[0].text == u'Тема не найдена':
        raise SkipTorrent('Torrent deleted')


def check_torrent_status(tree):
    """Raises if torrent status not found or status is a bad one"""
    good = [
        u'не проверено',
        u'проверено',
        u'недооформлено',
        u'сомнительно',
        u'временная'
    ]
    sel = cssselect.CSSSelector('#tor-reged #tor-status-resp > a > b')
    tags = sel(tree)
    if not tags:
        raise SkipTorrent('Status not found')

    status = tags[0].text
    if status not in good:
        raise SkipTorrent(u'Bad torrent status: {}'.format(status))



class Error(RuntimeError):
    """Generic parse error"""
    pass


class SkipTorrent(Error):
    """Raised for removed torrents etc"""
    pass
