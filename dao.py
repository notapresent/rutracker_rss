"""Data access layer"""
import datetime
from contextlib import contextmanager

from google.appengine.ext import ndb

from models import Torrent, Category, Account


# Generic functions

def get_from_key(key):
    """Return entity from key"""
    return key.get()


def write_multi(entities):
    """Write multiple entities at once"""
    ndb.put_multi(entities)


# Torrent-related functions

def latest_torrent_dt():
    """Returns datetime for most recent torrent or start of epoch if no torrents"""
    latest_torrent = Torrent.query().order(-Torrent.dt).get()
    if latest_torrent:
        return latest_torrent.dt
    else:
        return datetime.datetime.utcfromtimestamp(0)


def latest_torrents(num_items, cat_key=None):
    """Returns num_items torrent in specified category and/or its subcategories"""
    if cat_key is None:
        cat_key = root_category_key()

    return Torrent.query(ancestor=cat_key).order(-Torrent.dt).fetch(num_items)


def make_torrent(parent, fields):
    """Save torrent, identified by key"""
    return Torrent(parent=parent, **fields)


# Category-related functions

def root_category_key():
    """Returns root category key"""
    return ndb.Key(Category, 'r0')


def changed_cat_keys(dt):
    """Returns keys for categories, changed after specified time"""
    return Category.query().filter(Category.dirty == True).fetch(keys_only=True)

def unmark_dirty_categories(keys):
    """Reset dirty flag for all entities identified by keys """
    cats = ndb.get_multi(keys)
    for cat in cats:
        cat.dirty = False
    ndb.put_multi(cats)


def category_key_from_tuples(cat_tuples):
    """"Makes full category key from list of category tuples"""
    pairs = [(Category, '{}{}'.format(cat[1], cat[0])) for cat in cat_tuples]
    return ndb.Key(pairs=pairs)


def make_category(key, title):
    """Make category entity with key and title"""
    return Category(key=key, title=title)


# def make_categories(cat_list):
#     """Recursively create and return categories (without saving)"""
#     cat_tuple = cat_list.pop()
#     cat_key = category_key([cat_tuple])
#     cat = cat_get.get()



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

