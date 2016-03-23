"""Adds tasks to task queue"""
import pickle
from google.appengine.api import taskqueue


def add_feeds_update_task():
    """Enqueue task updating feeds"""
    taskqueue.add(url='/task/update_feeds')


def add_feed_build_tasks(params_list):
    """Enqueue task for building feed for specific category"""
    q = taskqueue.Queue()
    tasks = [taskqueue.Task(url='/task/build_feed', payload=pack_payload(p)) for p in params_list]
    q.add(tasks)


def add_torrent_tasks(params_list):
    """"Enqueue task for torrent entry represented by dict"""
    q = taskqueue.Queue()
    tasks = [taskqueue.Task(url='/task/torrent', payload=pack_payload(p)) for p in params_list]
    q.add(tasks)


def add_map_rebuild_task():
    """"Enqueue task for rebuilding category map"""
    taskqueue.add(url='/task/buildmap')


def pack_payload(value):
    """Pack value for use as task payload"""
    return pickle.dumps(value)


def unpack_payload(payload):
    """Unpack task payload"""
    return pickle.loads(payload)
