from datetime import datetime

import dao


class Scraper(object):
    """Extracts torrent data from tracker"""
    def __init__(self, webclient, parser):
        self.webclient = webclient
        self.parser = parser

    def get_new_torrents(self):
        """Returns list of torent entries for new torrents"""
        index_html = self.webclient.get_index_page()
        all_entries = self.parser.parse_index(index_html)
        return filter_new_entries(all_entries)

    def get_torrent_data(self, tid):
        """Returns data for torrent, specified by tid"""
        html = self.webclient.get_torrent_page(tid)
        entry = self.parser.parse_torrent_page(html)
        return entry


def filter_new_entries(entries):
    """Returns only new entries from the list"""
    dt_threshold = dao.latest_torrent_dt()     # XXX not sure where to put this
    return [e for e in entries if datetime.utcfromtimestamp(e['timestamp']) >= dt_threshold]
