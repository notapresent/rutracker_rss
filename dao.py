"""Data access layer"""
import datetime
from contextlib import contextmanager

from google.appengine.ext import ndb

from models import Torrent, Category, Account, FeedRebuildDate


ROOT_CATEGORY_KEY = ndb.Key(Category, 'r0')
FEED_REBUILD_KEY = ndb.Key(FeedRebuildDate, '0')


# Generic functions

def get_from_key(key):
    """Return entity from key"""
    return key.get()


def write_multi(entities):
    """Write multiple entities at once"""
    ndb.put_multi(entities)


def get_all_parents(key):
    """"Returns list of all parent keys for ndb key"""
    parent = key.parent()
    if parent:
        rv = get_all_parents(parent)
        rv.append(parent)
        return rv
    else:
        return []

def get_all_parents_multi(keys):
    """Returns all parents for multiple keys"""
    rv = set()
    for key in keys:
        rv.update(get_all_parents(key))
    return rv

# Torrent-related functions

def latest_torrent_dt():
    """Returns datetime for most recent torrent or start of epoch if no torrents"""
    latest_torrent = Torrent.query(ancestor=ROOT_CATEGORY_KEY).order(-Torrent.dt).get()
    if latest_torrent:
        return latest_torrent.dt
    else:
        return datetime.datetime.utcfromtimestamp(0)


def latest_torrents(num_items, cat_key=None):
    """Returns num_items torrent in specified category and/or its subcategories"""
    if cat_key is None:
        cat_key = ROOT_CATEGORY_KEY
    return Torrent.query(ancestor=cat_key).order(-Torrent.dt).fetch(num_items)


def make_torrent(parent, fields):
    """Save torrent, identified by key"""
    return Torrent(parent=parent, **fields)


# Category-related functions

def get_all_categories():
    """Returns all categories"""
    return Category.query(ancestor=ROOT_CATEGORY_KEY).fetch()


def all_changed_categories_since(dt):
    """Returns all categories with torrents added since dt"""
    changed_keys = set(changed_cat_keys_since(dt))
    changed_keys.update(get_all_parents_multi(changed_keys))
    return ndb.get_multi(changed_keys)


def changed_cat_keys_since(dt):
    """Returns category keys for categories with torrents added since dt"""
    new_torrent_keys = Torrent.query(Torrent.dt > dt).fetch(keys_only=True)
    cat_keys = [key.parent() for key in new_torrent_keys]
    return cat_keys


def dirty_categories():
    """Returns all categories, marked as dirty"""
    return Category.query().filter(Category.dirty == True).fetch()


def unmark_dirty_categories(keys):
    """Reset dirty flag for all entities identified by keys """
    cats = ndb.get_multi(keys)
    to_save = []
    for cat in cats:
        if cat.dirty:
            cat.dirty = False
            to_save.append(cat)
    ndb.put_multi(to_save)


def category_key_from_tuples(cat_tuples):
    """"Makes full category key from list of category tuples"""
    pairs = [(Category, '{}{}'.format(cat[1], cat[0])) for cat in cat_tuples]
    return ndb.Key(pairs=pairs)


def make_category(key, title):
    """Make category entity with key and title"""
    return Category(key=key, title=title)


# Account-related functions

def get_account():
    """Return one account"""
    return Account.query().get()


@contextmanager
def account_context(acc=None):
    """Provides account context and saves account entry if it was changed"""
    account = acc or get_account()
    values = account.to_dict()

    yield account

    if account.to_dict() != values:
        account.put()


#  Feed-related functions

def get_last_feed_rebuild_dt():
    """Returns datatime of last feed rebuild"""
    entity = FEED_REBUILD_KEY.get()
    if not entity:
        return datetime.datetime.utcfromtimestamp(0)

    return entity.dt


def set_last_feed_rebuild_dt(dt):
    """Saves datatime of last feed rebuild"""
    entity = FeedRebuildDate(key=FEED_REBUILD_KEY, dt=dt)
    entity.put()
