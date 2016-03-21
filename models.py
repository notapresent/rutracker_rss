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


class Account(ndb.Model):
    """Represents tracker user account along with its session"""
    username = ndb.StringProperty(indexed=False, required=True)
    password = ndb.StringProperty(indexed=False, required=True)
    userid = ndb.IntegerProperty(indexed=False, required=True)
    cookies = ndb.JsonProperty()

    def __repr__(self):
        return "<Account username='{}' userid='{}' cookies=[{}]>".format(
            self.username, self.userid, self.cookies and self.cookies.keys())


class Category(ndb.Model):
    """Represents category entry"""
    title = ndb.StringProperty(indexed=False, required=True)
    dirty = ndb.BooleanProperty(indexed=True, default=True)       # This flag is set when torrent is added to category


class PersistentScalarValue(ndb.Expando):
    """Persistent scalar value that is stored in datastore"""
    pass
