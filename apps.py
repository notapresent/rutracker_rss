import os
import webapp2
import logging

import handlers


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
loglevel = logging.DEBUG if debug else logging.INFO

logging.getLogger().setLevel(logging.DEBUG)     # XXX

task_app = webapp2.WSGIApplication([
    ('/task/index', handlers.IndexTaskHandler),
    ('/task/torrent', handlers.TorrentTaskHandler),
    ('/task/update_feeds', handlers.FeedTaskHandler),
    ('/task/buildmap', handlers.CategoryMapTaskHandler),
    ('/task/cleanup', handlers.JanitorTaskHandler)
], debug=debug)

manage_app = webapp2.WSGIApplication([
    ('/manage/', handlers.DashboardHandler),
], debug=debug)
