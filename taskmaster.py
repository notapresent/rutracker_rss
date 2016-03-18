from google.appengine.api.taskqueue import Queue, Task

import webclient


class TaskMaster(object):
    """Creates and enqueues tasks"""
    def __init__(self):
        self.queue = Queue()

    def add_feed_update_task(self):
        """Enqueue task updating feeds"""
        self.queue.add(Task(url='/task/update_feeds'))  # TODO make url a parameter

    def add_torrent_task(self, torrent_entry):
        """"Enqueue task for torrent entry represented by dict"""
        task = Task(url='/task/torrent', params=torrent_entry)  # TODO make url a parameter, use pickle 
        self.queue.add(task)

    def add_new_torrents(self, scraper):
        """Enqueues tasks for all new torrents"""
        try:
            new_entries = scraper.get_new_torrents()

        except webclient.NotLoggedIn:   # Session expired
            pass
        except webclient.RequestError:  # Tracker is down, happens sometimes
            pass
        else:
            for e in new_entries:
                self.add_torrent_task(e)
