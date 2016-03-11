import datetime
import os
from ttscraper import staticstorage


def debug_dump(filename, content):
    ts = datetime.datetime.utcnow().strftime('%d-%m-%Y_%H-%M-%S')
    path, suffix = os.path.splitext(filename)
    filename = "{}_{}{}".format(path, ts, suffix)

    if type(content) is unicode:
        content = content.encode('utf-8')

    storage = staticstorage.GCSStorage()
    storage.put(filename, content)

