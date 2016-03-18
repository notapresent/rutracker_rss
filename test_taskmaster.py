import unittest
from google.appengine.ext import testbed
from mock import Mock, patch

from taskmaster import TaskMaster


class TaskMasterTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        self.testbed.init_taskqueue_stub()
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()

    def test_add_torrent_task_enqueues(self):
        tm = TaskMaster()
        tm.add_torrent_task({})

        tasks = self.taskqueue_stub.get_filtered_tasks()
        self.assertEqual(len(tasks), 1)

    def test_add_feed_update_task_enqueues(self):
        tm = TaskMaster()
        tm.add_feed_update_task()

        tasks = self.taskqueue_stub.get_filtered_tasks()
        self.assertEqual(len(tasks), 1)

    def test_add_new_torrents_adds_all(self):
        fake_entries = [{} for _ in range(5)]
        mock_scraper = Mock(get_new_torrents=Mock(return_value=fake_entries))

        tm = TaskMaster()
        tm.add_new_torrents(mock_scraper)

        tasks = self.taskqueue_stub.get_filtered_tasks()
        self.assertEqual(len(tasks), len(fake_entries))
