"""(Re)builds feeds for categories"""
import os
import datetime
import jinja2
from google.appengine.api import app_identity

import dao
import util


def build_and_save_for_category(cat, store, prefix):
    """Build and save feeds for category"""
    feed = build_feed(cat)
    save_feeds(store, feed, prefix, cat.key.id())


def build_feed(cat):
    """Build feed for category"""
    feed = Feed(title=cat.title, link=get_app_url())
    items = dao.latest_torrents(feed_size(cat), cat.key)
    for item in items:
        feed.add_item(item)
    return feed


def get_app_url():
    """Returns full URL for app engine app"""
    app_id = app_identity.get_application_id()
    return 'http://{}.appspot.com/'.format(app_id)


def save_feeds(store, feed, prefix, name):
    """Saves feeds to storage"""
    xml = feed.render_short_rss()
    path = os.path.join(prefix, 'short', '{}.xml'.format(name))
    store.put(path, xml.encode('utf-8'), 'application/rss+xml')


class Feed(object):
    """Represents feed with torrent entries"""

    def __init__(self, title, link, ttl=60, description=None):
        self.title = title
        self.link = link
        self.description = description or title
        self.ttl = ttl
        self.items = []
        self.lastBuildDate = None
        self.latest_item_dt = datetime.datetime.utcfromtimestamp(0)

    def add_item(self, item):
        self.items.append(item)
        if self.latest_item_dt < item.dt:
            self.latest_item_dt = item.dt

    def render_short_rss(self):
        self.lastBuildDate = self.latest_item_dt
        env = make_jinja_env()
        template = env.get_template('rss_short.xml')
        return template.render(feed=self)


def make_jinja_env():
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'),
        # loader=PackageLoader('package_name', 'templates'),
        autoescape=True,
        extensions=['jinja2.ext.autoescape']
    )
    jinja2_env.filters['rfc822date'] = util.datetime_to_rfc822
    return jinja2_env


def feed_size(category):
    """Returns number of feed entries for category"""
    if category.key.id() == 'r0':               # Root category
        return 100
    elif category.key.id().startswith('c'):     # Level 2 category
        return 50
    return 25                                   # category with subcategories
