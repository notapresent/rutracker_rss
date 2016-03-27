# coding: utf-8
"""Everythong related to parsing tracker responses"""
import sys
import datetime
import urlparse

from lxml import etree, cssselect


class Parser(object):
    def parse_index(self, html):
        try:
            rows = self.parse_index_table(html)
            entries = [self.parse_index_row(row) for row in rows]
        except IndexError as e:
            _, old_exc, traceback = sys.exc_info()
            exc = ParseError(old_exc.message, html=html, slug='torrent_index')
            raise exc, None, traceback

        return entries

    def parse_torrent_page(self, html):
        tree = make_tree(html)
        validate_torrent(tree)

        try:
            categories = self.torrent_categories(tree)
            btih = self.torrent_btih(tree)
            description = self.torrent_description(tree)

        except IndexError as e:
            _, old_exc, traceback = sys.exc_info()
            exc = ParseError(old_exc.message, html=html, slug='torrent_entry')
            raise exc, None, traceback

        torrent_data = {
            'description': description,
            'btih': btih
        }

        return (torrent_data, categories)

    def parse_index_table(self, html):
        tree = make_tree(html)
        """Returns list of index rows represented as etree.Elements"""
        rows_selector = cssselect.CSSSelector('table#tor-tbl tr.tCenter.hl-tr')
        rows = rows_selector(tree)
        return rows

    def parse_index_row(self, row):
        """Parse index row represented by lxml element and return dict"""
        tid = self.index_tid(row)
        title = self.index_title(row)
        dt = self.index_dt(row)
        nbytes = self.index_nbytes(row)

        return {
            'id': tid,
            'title': title,
            'dt': dt,
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
        return unicode(a.text)

    def index_dt(self, elem):
        timestamp_selector = cssselect.CSSSelector('td:last-child u')
        timestamp = timestamp_selector(elem)[0].text
        return datetime.datetime.utcfromtimestamp(int(timestamp))

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
        desc = desc_selector(tree)[0]

        contents_list = [etree.tostring(e, encoding='utf-8') for e in desc.iterchildren() if not is_garbage(e)]
        desc_str = ''.join(contents_list)
        return desc_str.strip()

    def torrent_btih(self, tree):
        btih_link_selector = cssselect.CSSSelector('a.med.magnet-link-16')
        elem = btih_link_selector(tree)[0]

        return btih_from_href(elem.attrib['href'])


def is_garbage(elem):
    """Returns True for unwanted elements in torrent description"""
    if elem.attrib.get('id') == 'tor-reged':
        return True

    if elem.tag == 'div' and elem.attrib.get('class') in ['clear', 'spacer_12']:
        return True

    if elem.tag is etree.Comment:
        return True

    return False


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



class ParseError(RuntimeError):
    """Generic parse error"""
    def __init__(self, message, **kwargs):
        self.__dict__.update(kwargs)
        RuntimeError.__init__(self, message)



class SkipTorrent(RuntimeError):
    """Raised for removed torrents etc"""
    pass
