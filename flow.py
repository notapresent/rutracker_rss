"""Orchestrates import process flow"""
import datetime
import json

import dao
import staticstorage
import webclient, parsers



def import_index(taskmaster):
    """Add tasks for new torrents"""
    num_new_torrents = add_new_torrents(taskmaster)

    if num_new_torrents:
        taskmaster.add_feed_update_task()

    return num_new_torrents


def add_new_torrents(taskmaster):
    """Enqueues tasks for all new torrents"""
    wc = webclient.RutrackerWebClient()
    p = parsers.Parser()
    try:
        new_entries = get_new_torrents(wc, p)

    except webclient.NotLoggedIn:   # Session expired
        pass
    except webclient.RequestError:  # Tracker is down, happens sometimes
        pass
    else:
        for e in new_entries:
            taskmaster.add_torrent_task(e)

        return len(new_entries)


def import_torrent(torrent_data):
    """Run torrent import task for torrent, specified by torrent_data"""
    tid = int(torrent_data['tid'])
    wc = webclient.RutrackerWebClient()
    p = parsers.Parser()

    torrent_data.update(get_torrent_data(wc, p, tid))  # TODO handle 'torrent deleted' and other errors here
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


def rebuild_category_map():
    """Rebuilds category map file"""
    all_cats = dao.get_all_categories()
    tree = build_category_tree(all_cats)
    map_json = json.dumps([tree], separators=(',', ':'), ensure_ascii=False)
    storage = staticstorage.GCSStorage()
    storage.put('category_map.json', map_json.encode('utf-8'), 'application/json')


def build_category_tree(cat_list):
    cmap = {}
    for cat in cat_list:
        cat_id = cat.key.id()
        parent_id = cat.key.parent().id() if cat.key.parent() else None
        cmap[cat_id] = {'cid': cat_id, 'text': cat.title, 'parent_id': parent_id}

    for cat_id, cat in cmap.items():
        parent_id = cat.pop('parent_id')
        if not parent_id:
            continue

        parent = cmap[parent_id]

        if 'nodes' not in parent:
            parent['nodes'] = []

        assert cat not in parent['nodes']
        parent['nodes'].append(cat)

    return cmap['r0']


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


def get_new_torrents(webclient, parser):
    """Returns list of torent entries for new torrents"""
    index_html = webclient.get_index_page()
    all_entries = parser.parse_index(index_html)
    return filter_new_entries(all_entries)


def get_torrent_data(webclient, parser, tid):
    """Returns data for torrent, specified by tid"""
    html = webclient.get_torrent_page(tid)
    entry = parser.parse_torrent_page(html)
    return entry


def filter_new_entries(entries):
    """Returns only new entries from the list"""
    dt_threshold = dao.latest_torrent_dt()
    return [e for e in entries if datetime.datetime.utcfromtimestamp(e['timestamp']) > dt_threshold]

