import datetime
import os
import logging
from contextlib import contextmanager

from google.appengine.api.runtime import runtime

import staticstorage


def debug_dump(filename, content, storage=None):
    """Create debug dump file with specified name and content"""
    ts = datetime.datetime.utcnow().strftime('%d-%m-%Y_%H-%M-%S')
    path, suffix = os.path.splitext(filename)
    filename = "{}_{}{}".format(path, ts, suffix)

    if type(content) is unicode:
        content = content.encode('utf-8')

    store = storage or staticstorage.GCSStorage()
    store.put(filename, content)


@contextmanager
def trace():
    mem_usage = runtime.memory_usage()
    before = mem_usage.current()

    try:
        yield
    finally:
        mem_usage = runtime.memory_usage()
        after = mem_usage.current()
        a1m = mem_usage.average1m()
        a10m = mem_usage.average10m()
        logging.debug(' --- MEMTRACE: CURRENT={} DELTA={}M AVG: {}/{} ---'.format(after, after - before, a1m, a10m))
