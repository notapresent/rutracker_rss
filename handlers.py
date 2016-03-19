import webapp2
import json

import flow
from taskmaster import TaskMaster
import feeds
import staticstorage
import dao
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
        num_new = flow.import_index(taskmaster)
        return {
            'status': 'success',
            'message': '{} new torrent tasks added'.format(num_new),
        }


class TorrentTaskHandler(webapp2.RequestHandler):
    """Starts individual torrent import task"""

    def post(self):
        torrent_data = self.request.POST
        flow.import_torrent(torrent_data)


class FeedTaskHandler(JSONHandler):
    """Starts feed rebuild task"""

    def post(self):
        last_rebuild_dt = dao.get_last_feed_rebuild_dt()
        changed_categories = dao.all_changed_categories_since(last_rebuild_dt)
        store = staticstorage.GCSStorage()

        for cat in changed_categories:
            feeds.build_and_save_for_category(cat, store, 'feeds')

        dao.set_last_feed_rebuild_dt(dao.latest_torrent_dt())

        return {
            'status': 'success',
            'message': '{} feeds changed since {}'.format(len(changed_categories), last_rebuild_dt),
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
