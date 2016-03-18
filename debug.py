import datetime
import os
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
