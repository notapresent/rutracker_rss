import webapp2

from ttscraper import flow
from ttscraper.scraper import Scraper
from ttscraper.taskmaster import TaskMaster
from ttscraper import feeds, staticstorage, dao
from ttscraper.janitor import Janitor

from rutracker import WebClient, Parser


class IndexTaskHandler(webapp2.RequestHandler):
    """Starts tracker scraping task"""
    def get(self):
        taskmaster = TaskMaster()
        scraper = Scraper(WebClient(), Parser())
        flow.start(taskmaster, scraper)


class TorrentTaskHandler(webapp2.RequestHandler):
    """Starts individual torrent import task"""
    def post(self):
        torrent_data = self.request.POST
        scraper = Scraper(WebClient(), Parser())
        flow.import_torrent(torrent_data, scraper)


class FeedTaskHandler(webapp2.RequestHandler):
    """Starts feed rebuild task"""
    def post(self):
        changed_keys = dao.changed_cat_keys(None)   # TODO pass last feed rebuild date here
        store = staticstorage.GCSStorage()
        for cat_key in changed_keys:
            feeds.build_and_save_for_category(cat_key, store, 'feeds')


class JanitorTaskHandler(webapp2.RequestHandler):
    def post(self):
        janitor = Janitor()
        janitor.run()


class DashboardHandler(webapp2.RequestHandler):
    def get(self):
        env = self.request.environ.items()
        self.response.headers['Content-Type'] = 'text/plain'
        env_vars = ["%s: %s" % (k, v) for k, v in env]
        self.response.out.write("\n".join(env_vars))
