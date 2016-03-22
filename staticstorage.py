"""Static data storage"""
import cloudstorage as gcs
from google.appengine.api import app_identity


class BaseStaticStorage(object):
    """Base class for storage adapters. All subclasses must implement put and url_for_path methods"""
    def put(self, path, content):
        """Put object into storage at specified path"""
        raise NotImplementedError()

    def url_for_path(self, path):
        """Get absolute url for object stored at path"""
        raise NotImplementedError()


class GCSStorage(BaseStaticStorage):
    """Google cloud storage backend"""
    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or app_identity.get_default_gcs_bucket_name()

    def make_full_path(self, path):
        """Build full path from bucket name and given file path"""
        return '/' + self.bucket_name + '/' + path.strip('/')

    def put(self, path, content, content_type='text/html'):
        fullname = self.make_full_path(path)
        gcs_file = gcs.open(fullname, 'w', content_type=content_type)
        try:
            gcs_file.write(content)
        finally:
            gcs_file.close()

    def url_for_path(self, path):
        return 'https://storage.googleapis.com/{}.appspot.com/{}'.format(self.bucket_name, path.strip('/'))
