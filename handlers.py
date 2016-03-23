import webapp2
import json

import flow
from debug import trace


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
        with trace():
            num_new = flow.import_index()
        return {
            'status': 'success',
            'message': '{} new torrent tasks added'.format(num_new),
        }


class TorrentTaskHandler(webapp2.RequestHandler):
    """Starts individual torrent import task"""
    def post(self):
        with trace():
            flow.import_torrent(self.request.body)


class FeedsTaskHandler(JSONHandler):
    """Starts feed build task"""
    def post(self):
        with trace():
            last_rebuild_dt, changed_categories = flow.add_feed_tasks()
        return {
            'status': 'success',
            'message': '{} feeds changed since {}'.format(changed_categories, last_rebuild_dt)
        }


class SingleFeedTaskHandler(JSONHandler):
    """Starts feed build task"""
    def post(self):
        with trace():
            rv = flow.build_feed(self.request.body)
        return {
            'status': 'success',
            'message': 'Feed {} rebuilt'.format(rv)
        }


class CategoryMapTaskHandler(JSONHandler):
    """Starts task for rebuilding category map file"""
    def post(self):
        with trace():
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
