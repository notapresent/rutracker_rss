import webapp2

from ttscraper import flow
from ttscraper.scraper import Scraper
from ttscraper.taskmaster import TaskMaster
from rutracker import WebClient, Parser


class IndexTaskHandler(webapp2.RequestHandler):
    """Starts tracker scraping task"""
    def post(self):
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
    def post(self):
        pass    # TODO


class JanitorTaskHandler(webapp2.RequestHandler):
    def post(self):
        pass    # TODO


class DashboardHandler(webapp2.RequestHandler):
    def get(self):
        env = self.request.environ.items()
        self.response.headers['Content-Type'] = 'text/plain'
        env_vars = ["%s: %s" % (k, v) for k, v in env]
        self.response.out.write("\n".join(env_vars))
