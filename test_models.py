import datetime
import unittest
import logging

from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

from models import Account, Torrent


class DatastoreTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

        # Create a consistency policy that will simulate the High Replication
        # consistency model.
        self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        # Initialize the datastore stub with this policy.
        self.testbed.init_datastore_v3_stub(consistency_policy=self.policy)
        self.testbed.init_memcache_stub()
        # Clear ndb's in-context cache between tests.
        ndb.get_context().clear_cache()

        self._logger = logging.getLogger()
        self._old_logging_level = self._logger.getEffectiveLevel()
        self._logger.setLevel(logging.ERROR)

    def tearDown(self):
        self.testbed.deactivate()
        self._logger.setLevel(self._old_logging_level)


class AccountTestCase(DatastoreTestCase):
    def setUp(self):
        super(AccountTestCase, self).setUp()
        self.username = 'testuser'
        self.password = 'testpassword'
        self.userid = 123

    def test_account_is_stored(self):
        acc = Account(username=self.username, password=self.password, userid=self.userid)
        key = acc.put()
        stored = key.get()

        self.assertEqual(stored.username, self.username)
        self.assertEqual(stored.password, self.password)
        self.assertEqual(stored.userid, self.userid)

    def test_username_is_required(self):
        acc = Account(password=self.password, userid=self.userid)
        with self.assertRaises(BadValueError):
            acc.put()

    def test_password_is_required(self):
        acc = Account(username=self.username, userid=self.userid)
        with self.assertRaises(BadValueError):
            acc.put()

    def test_userid_is_required(self):
        acc = Account(password=self.password, username=self.username)
        with self.assertRaises(BadValueError):
            acc.put()

    def test_get_one_returns_entity(self):
        acc = Account(username=self.username, password=self.password, userid=self.userid)
        acc.put()

        result = Account.get_one()

        self.assertEqual(acc, result)


class TorrentTestCase(DatastoreTestCase):
    def setUp(self):
        super(TorrentTestCase, self).setUp()
        self.title = 'Torrent title'
        self.btih = '1234567890ABCDEF'
        self.nbytes = 1234567890
        self.dt = datetime.datetime.now()

    def test_required_fields_are_required(self):
        no_title = Torrent(btih=self.btih, nbytes=self.nbytes, dt=self.dt)
        no_btih = Torrent(title=self.title, nbytes=self.nbytes, dt=self.dt)
        no_nbytes = Torrent(title=self.title, btih=self.btih, dt=self.dt)
        no_dt = Torrent(title=self.title, btih=self.btih, nbytes=self.nbytes)

        with self.assertRaises(BadValueError):
            no_title.put()

        with self.assertRaises(BadValueError):
            no_btih.put()

        with self.assertRaises(BadValueError):
            no_nbytes.put()

        with self.assertRaises(BadValueError):
            no_dt.put()

    def test_get_latest_dt_returns_lstest(self):
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(1)
        t1 = Torrent(title=self.title, btih=self.btih, nbytes=self.nbytes, dt=yesterday)
        t2 = Torrent(title=self.title, btih=self.btih, nbytes=self.nbytes, dt=now)
        t1.put()
        t2.put()

        rv = Torrent.get_latest_dt()

        self.assertEqual(rv, now)
