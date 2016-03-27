# coding: utf-8
"""Webclient is responsible for comunicating with tracker via HTTP"""
import logging
import requests

import dao


TIMEOUTS = (3.05, 10)       # Connect, read


class BaseWebClient(object):
    """Base class for tracker adapters"""
    ENCODING = 'utf-8'      # Default encoding for text responses

    def __init__(self, session=None):
        self.session = session or requests.Session()
        # Set logging level for libraries
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def request(self, url, method='GET', **kwargs):
        """Send an actual http request, raise Error on error"""
        try:
            resp = self.session.request(method, url, timeout=TIMEOUTS, **kwargs)
            if not resp.ok:
                resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RequestError(str(e))

        return resp

    def user_request(self, account, url, method='GET',  **kwargs):
        """Send request on behalf of tracker user, handle session cookies"""
        if account.cookies:
            self.session.cookies.update(account.cookies)
        else:
            self.tracker_log_in(account)
            account.cookies = self.session.cookies.get_dict()

        try:
            resp = self.authorized_request(account, url, method,  **kwargs)
        except NotLoggedIn as e:
            account.cookies = None
            raise

        return resp

    def authorized_request(self, account, url, method,  **kwargs):
        """Issue HTTP request and raise NotLoggedIn if user was not authorised on server"""
        resp = self.request(url, method, **kwargs)
        html = self.get_text(resp)

        if html and not self.is_logged_in(html, account):
            raise NotLoggedIn('User {} is not logged in'.format(account))

        return resp

    def get_text(self, response):
        """Returns response text for text responses, None for non-text"""
        if 'text' in response.headers['content-type']:
            response.encoding = self.ENCODING
            return response.text

    def is_logged_in(self, html, account):
        """Returns true if html response has user account info"""
        return account.userid in html


class RutrackerWebClient(BaseWebClient):
    """Tracker-specific adapter"""
    TORRENT_PAGE_URL = 'http://rutracker.org/forum/viewtopic.php?t={}'
    LOGIN_URL = 'http://login.rutracker.org/forum/login.php'
    INDEX_URL = 'http://rutracker.org/forum/tracker.php'
    INDEX_FORM_DATA = {'prev_new': 0, 'prev_oop': 0, 'f[]': -1, 'o': 1, 's': 2, 'tm': -1, 'oop': 1}
    ENCODING = 'windows-1251'
    USER_MARKER = ('<a class="logged-in-as-uname" '
                   'href="http://rutracker.org/forum/profile.php?mode=viewprofile&amp;u={}">')

    def get_torrent_page(self, account, tid):
        """"Returns torrent page content"""
        url = self.TORRENT_PAGE_URL.format(tid)
        resp = self.user_request(account, url)
        return self.get_text(resp)

    def get_index_page(self, account, forum_id=None):
        """Returns page with latest torrents list"""
        formdata = dict(self.INDEX_FORM_DATA)
        if forum_id is None:
            url = self.INDEX_URL
        else:
            url = self.INDEX_URL + '?f=' + str(forum_id)
            formdata['f[]'] = str(forum_id)
        resp = self.user_request(account, url, method='POST', data=formdata)
        return self.get_text(resp)

    def tracker_log_in(self, account):
        """Log in user via tracker log in form, returns True if login succeeded"""
        formdata = RutrackerWebClient.login_form_data(account)

        resp = self.request(self.LOGIN_URL, method='POST', data=formdata)
        html = self.get_text(resp)

        if html and not RutrackerWebClient.is_logged_in(html, account):
            raise LoginFailed("Server login failed for {} ".format(account))

    @classmethod
    def is_logged_in(cls, html, account):
        """Check if the page was requested with user logged in"""
        marker = cls.USER_MARKER.format(account.userid)
        return marker in html

    @classmethod
    def login_form_data(cls, account):
        return {
            'login_password': account.password,
            'login_username': account.username,
            'login': 'Whatever'        # Must be non-empty
        }


class Error(RuntimeError):
    """Base class for all exceptions in this module"""
    pass


class RequestError(Error):
    """HTTP-level error"""
    pass


class LoginFailed(Error):
    """Server login failed"""
    pass


class NotLoggedIn(Error):
    """User is not logged in"""
    pass
