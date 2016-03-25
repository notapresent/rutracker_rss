"""Data access layer"""
import datetime
from contextlib import contextmanager
import logging

from google.appengine.ext import ndb
from google.appengine.api import memcache

from models import Torrent, Category, Account, PersistentScalarValue


ROOT_CATEGORY_KEY = ndb.Key(Category, 'r0')
_account_key = None



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
    keys = Torrent.query(ancestor=cat_key).order(-Torrent.dt).fetch(num_items, keys_only=True, max_memcache_items=100)
    return ndb.get_multi(keys, max_memcache_items=100)


def make_torrent(parent, fields):
    """Save torrent, identified by key"""
    return Torrent(parent=parent, **fields)


def torrent_keys_since_dt(dt):
    """Returns list of keys for torrents added since dt"""
    return Torrent.query(Torrent.dt > dt).fetch(keys_only=True)


# Category-related functions

def get_all_categories():
    """Returns all categories"""
    return Category.query(ancestor=ROOT_CATEGORY_KEY).fetch()


def all_changed_categories_since(dt):
    """Returns all categories with torrents added since dt"""
    changed_keys = set(changed_cat_keys_since(dt))
    changed_keys.update(get_all_parents_multi(changed_keys))
    return ndb.get_multi(changed_keys)


def dirty_categories():
    """Returns all categories, marked as dirty"""
    return Category.query().filter(Category.dirty == True).fetch()      # noqa


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
    """Return one account and cache account key for future reuse if needed"""
    global _account_key
    if _account_key:
        return _account_key.get()

    acc = Account.query().get()
    _account_key = acc.key
    return acc


@contextmanager
def account_context(acc=None):
    """Provides account context and saves account entry if it was changed"""
    account = acc or get_account()
    values = account.to_dict()

    try:
        yield account
    finally:
        if account.to_dict() != values:
            account.put()


#  Feed-related functions

def get_last_feed_rebuild_dt():
    """Returns datatime of last feed rebuild"""
    cts = CachedPersistentValue('feed_build_date')
    return cts.get() or datetime.datetime.utcfromtimestamp(0)


def set_last_feed_rebuild_dt(dt):
    """Saves datatime of last feed rebuild"""
    cts = CachedPersistentValue('feed_build_date')
    cts.put(dt)


class CachedPersistentValue(object):
    root_key = ndb.Key('PersistentScalarValues', 'root')
    def __init__(self, key):
        self.key = 'cts.{}'.format(key)
        self.ds_key = ndb.Key(PersistentScalarValue, key, parent=self.root_key)

    def put(self, value, async=False):
        if not memcache.set(self.key, value):
            logging.debug("Failed to save to memcache %s -> %s", self.key, value)
            memcache.delete(self.key)
        psv = PersistentScalarValue(key=self.ds_key, value=value)
        if async:
            psv.put_async()
        else:
            psv.put()

    def get(self):
        val = memcache.get(self.key)
        if val is not None:
            return val

        entity = self.ds_key.get()
        if entity is None:
            return None

        memcache.set(self.key, entity.value)
        return entity.value

    def delete(self, async=False):
        memcache.delete(self.key)
        if async:
            self.ds_key.delete_async()
        else:
            self.ds_key.delete()
