"""Orchestrates import process flow"""
import datetime
import json
import logging

import dao
import feeds
import staticstorage
import webclient
import parsing
import taskmaster


def import_index():
    """Add tasks for new torrents"""
    num_new_torrents = add_new_torrents()

    if num_new_torrents:
        taskmaster.add_feeds_update_task()

    return num_new_torrents


def add_new_torrents():
    """Enqueues tasks for all new torrents"""
    wc = webclient.RutrackerWebClient()
    p = parsing.Parser()
    try:
        new_entries = get_new_torrents(wc, p)

    except webclient.NotLoggedIn:   # Session expired
        logging.debug('Session expired')
    except webclient.RequestError:  # Tracker is down, happens sometimes
        logging.debug('Tracker seems to be down')
    else:
        taskmaster.add_torrent_tasks(new_entries)
        return len(new_entries)


def import_torrent(payload):
    """Run torrent import task for torrent, specified by torrent_data"""
    torrent_dict = taskmaster.unpack_payload(payload)
    tid = torrent_dict['id']

    wc = webclient.RutrackerWebClient()
    with dao.account_context() as account:
        html = wc.get_torrent_page(account, tid)
    p = parsing.Parser()
    try:
        torrent_data, category_tuples = p.parse_torrent_page(html)
    except parsing.SkipTorrent as e:
        logging.info('Skipping torrent %d: %s', tid, str(e))
        return

    torrent_dict.update(torrent_data)
    to_write = process_categories(category_tuples)

    cat_key = dao.category_key_from_tuples(category_tuples)
    torrent = dao.make_torrent(cat_key, torrent_dict)
    to_write.append(torrent)

    dao.write_multi(to_write)


def process_categories(cat_tuples):
    """Create torrent category if needed. Returns list of entities to be saved"""
    cat_key = dao.category_key_from_tuples(cat_tuples)
    cat = dao.get_from_key(cat_key)

    if not cat:
        enqueue_map_rebuild_if_needed()
        return make_categories(cat_tuples)

    return []


def enqueue_map_rebuild_if_needed():
    rebuild_flag = dao.CachedPersistentValue('map_rebuild_flag')
    if not rebuild_flag.get():
        rebuild_flag.put(True)
        taskmaster.add_map_rebuild_task()


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
    rebuild_flag = dao.CachedPersistentValue('map_rebuild_flag')
    rebuild_flag.put(False)


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


def get_new_torrents(webclient, parser):
    """Returns list of torent entries for new torrents"""
    with dao.account_context() as account:
        index_html = webclient.get_index_page(account)
    all_entries = parser.parse_index(index_html)
    return filter_new_entries(all_entries)


def filter_new_entries(entries):
    """Returns only new entries from the list"""
    dt_threshold = dao.latest_torrent_dt()
    return [e for e in entries if e['dt'] > dt_threshold]


def add_feed_tasks():
    """Adds tasks for rebuilding feeds"""
    last_rebuild_dt = dao.get_last_feed_rebuild_dt()
    dao.set_last_feed_rebuild_dt(dao.latest_torrent_dt())
    cat_keys = changed_cat_keys_since(last_rebuild_dt)
    taskmaster.add_feed_build_tasks(cat_keys)
    logging.debug("Added %d feed rebuild tasks", len(cat_keys))
    return last_rebuild_dt, len(cat_keys)


def changed_cat_keys_since(dt):
    """Returns category keys for categories with torrents added since dt (including parents)"""
    new_torrent_keys = dao.torrent_keys_since_dt(dt)
    name2cat = {}
    for torrent_key in new_torrent_keys:
        cat_key = torrent_key.parent()
        name2cat.setdefault(cat_key.id(), cat_key)

        for pk in dao.get_all_parents(cat_key):
            name2cat.setdefault(pk.id(), pk)

    return name2cat.values()


def build_feed(payload_data):
    """Rebuilds feed for category"""
    category_key = taskmaster.unpack_payload(payload_data)
    category = dao.get_from_key(category_key)
    store = staticstorage.GCSStorage()
    feeds.build_and_save_for_category(category, store, 'feeds')
