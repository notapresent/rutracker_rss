"""Orchestrates import process flow"""
import datetime

import dao


def start(taskmaster, scraper):     # TODO needs a better name
    """Initiate torrent import process"""
    taskmaster.add_new_torrents(scraper)
    taskmaster.add_feed_update_task()   # TODO only run if there were torrent tasks


def import_torrent(torrent_data, scraper):
    """Run torrent import task for torrent, specified by torrent_data"""
    tid = int(torrent_data['tid'])
    torrent_data.update(scraper.get_torrent_data(tid))  # TODO handle 'torrent deleted' and other errors here
    cat_tuples = torrent_data.pop('categories')
    torrent_data = prepare_torrent(torrent_data)

    to_write = process_categories(cat_tuples)

    cat_key = dao.category_key_from_tuples(cat_tuples)
    torrent = dao.make_torrent(cat_key, torrent_data)
    to_write.append(torrent)

    dao.write_multi(to_write)


def process_categories(cat_tuples):
    """Create torrent category or mark it as diry if needed. Returns list of entities to be saved"""
    cat_key = dao.category_key_from_tuples(cat_tuples)
    cat = dao.get_from_key(cat_key)

    if not cat:
        return make_categories(cat_tuples)

    if not cat.dirty:
        cat.dirty = True
        return [cat]

    return []



def make_categories(cat_tuples):
    """Create and return entities for category and all its parent categories

    If category already exists, this function returns empty list"""
    tuples_copy = list(cat_tuples)
    rv = []

    while tuples_copy:
        key = dao.category_key_from_tuples(tuples_copy)
        cat = key.get()
        if cat:
            break
        _, _, cat_title = tuples_copy.pop()
        cat = dao.make_category(key, cat_title)
        rv.append(cat)

    return rv


def prepare_torrent(torrent_data):      # TODO move this
    """Prepare torrent field values"""
    return {
        'id': int(torrent_data['tid']),
        'title': torrent_data['title'],
        'dt': datetime.datetime.utcfromtimestamp(int(torrent_data['timestamp'])),
        'nbytes': int(torrent_data['nbytes']),
        'btih': torrent_data['btih'],
        'description': torrent_data['description']
    }
