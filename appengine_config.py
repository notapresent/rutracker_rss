from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add('lib')

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = recording.appstats_wsgi_middleware(app)
  return app
