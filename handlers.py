import webapp2
import json

import flow
from scraper import Scraper
from taskmaster import TaskMaster
import feeds, staticstorage, dao
from janitor import Janitor

from webclient import RutrackerWebClient
from parsers import Parser


class JSONHandler(webapp2.RequestHandler):
    """Base class for handlers returning JSON"""
    def initialize(self, request, response):
        super(JSONHandler, self).initialize(request, response)
        self.response.headers['Content-Type'] = 'application/json'

    def dispatch(self):
        rv = super(JSONHandler, self).dispatch()
        self.response.out.write(json.dumps(rv))


class IndexTaskHandler(JSONHandler):
    """Starts tracker scraping task"""
    def get(self):
        taskmaster = TaskMaster()
        scraper = Scraper(RutrackerWebClient(), Parser())
        num_new = flow.import_index(taskmaster, scraper)
        return {
            'status': 'success',
            'message': '{} new torrent tasks added'.format(num_new),
        }


class TorrentTaskHandler(webapp2.RequestHandler):
    """Starts individual torrent import task"""
    def post(self):
        torrent_data = self.request.POST
        scraper = Scraper(RutrackerWebClient(), Parser())
        flow.import_torrent(torrent_data, scraper)


class FeedTaskHandler(JSONHandler):
    """Starts feed rebuild task"""
    def post(self):
        changed_keys = dao.changed_cat_keys(None)
        dao.unmark_dirty_categories(changed_keys)
        store = staticstorage.GCSStorage()
        for cat_key in changed_keys:
            feeds.build_and_save_for_category(cat_key, store, 'feeds')

        return {
            'status': 'success',
            'message': '{} feeds rebuilt'.format(len(changed_keys)),
        }


class CategoryMapTaskHandler(JSONHandler):
    """Starts task for rebuilding category map file"""
    def post(self):
        flow.rebuild_category_map()
        return {
            'status': 'success',
            'message': 'Category map rebuilt',
        }


class JanitorTaskHandler(webapp2.RequestHandler):
    def post(self):
        janitor = Janitor()
        janitor.run()


class DashboardHandler(webapp2.RequestHandler):
    def get(self):      # TODO
        env = self.request.environ.items()
        self.response.headers['Content-Type'] = 'text/plain'
        env_vars = ["%s: %s" % (k, v) for k, v in env]
        self.response.out.write("\n".join(env_vars))
