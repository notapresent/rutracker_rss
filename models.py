"""All datastore models live in this module"""
import datetime

from google.appengine.ext import ndb


class Torrent(ndb.Model):
    """A main model for representing an individual Torrent entry."""
    title = ndb.StringProperty(indexed=False, required=True)
    btih = ndb.StringProperty(indexed=False, required=True)         # Infohash
    dt = ndb.DateTimeProperty(required=True)                        # Create/update time, as reported by tracker
    nbytes = ndb.IntegerProperty(indexed=False, required=True)      # Torrent data size, bytes
    description = ndb.TextProperty(required=True)
    forum_id = ndb.IntegerProperty(required=True)     # for finding torrents in category but not its subcategories

    _memcache_timeout = 2592000     # 30 days


class Account(ndb.Model):
    """Represents tracker user account along with its session"""
    username = ndb.StringProperty(indexed=False, required=True)
    password = ndb.StringProperty(indexed=False, required=True)
    userid = ndb.IntegerProperty(indexed=False, required=True)
    cookies = ndb.JsonProperty()

    _memcache_timeout = 86400       # 1 day

    def __repr__(self):
        return "<Account username='{}' userid='{}' cookies=[{}]>".format(
            self.username, self.userid, self.cookies and self.cookies.keys())


class Category(ndb.Model):
    """Represents category entry"""
    title = ndb.StringProperty(indexed=False, required=True)

    _memcache_timeout = 86400       # 1 day


class PersistentScalarValue(ndb.Expando):
    """Persistent scalar value that is stored in datastore"""
    pass
