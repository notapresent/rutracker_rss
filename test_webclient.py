import unittest
from google.appengine.ext import testbed
from mock import Mock, MagicMock, patch
import requests
from betamax import Betamax
from betamax.fixtures.unittest import BetamaxTestCase

from webclient import BaseWebClient, WebClient, Error, NotLoggedIn, TIMEOUTS


with Betamax.configure() as config:
    config.cassette_library_dir = '../cassettes'


class URLFetchTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_urlfetch_stub()

        self.session = MagicMock()

    def tearDown(self):
        self.testbed.deactivate()


class BaseWebClientTestCase(URLFetchTestCase):

    def test_request_calls_request(self):
        url = 'http://example.com/'
        webclient = BaseWebClient(self.session)
        resp = webclient.request(url)
        self.assertTrue(self.session.request.called)

    def test_request_raises(self):
        failed_resp = Mock(ok=False, status_code=500)
        failed_resp.raise_for_status = Mock(side_effect=requests.exceptions.RequestException)
        self.session.request = Mock(return_value=failed_resp)

        wc = BaseWebClient(self.session)
        with self.assertRaises(Error):
            wc.request('http://example.com/')

    def test_authorized_request_returns_response(self):
        mock_response = MagicMock()
        self.session.request = Mock(return_value=mock_response)
        wc = BaseWebClient(self.session)

        resp = wc.authorized_request(Mock(), 'http://example.com/', 'GET')

        self.assertIs(mock_response, resp)

    @patch('webclient.BaseWebClient.is_logged_in')
    def test_authorized_request_raises(self, is_logged_in):
        is_logged_in.return_value = False
        mock_response = MagicMock(headers={'content-type': 'text/html'})
        self.session.request = Mock(return_value=mock_response)
        wc = BaseWebClient(self.session)

        with self.assertRaises(NotLoggedIn):
            wc.authorized_request(Mock(), 'http://example.com/', 'GET')

    def test_get_text_returns_text(self):
        mock_response = MagicMock(headers={'content-type': 'text/html'}, text='some text')
        wc = BaseWebClient(None)

        rv = wc.get_text(mock_response)

        self.assertEqual(rv, 'some text')

    def test_get_text_returns_none_for_binary(self):
        mock_response = MagicMock(headers={'content-type': 'application/blah'})
        wc = BaseWebClient(None)

        rv = wc.get_text(mock_response)

        self.assertIs(rv, None)

    def test_user_request_updates_session_cookies(self):
        cookies = {'test name': 'test value'}
        mock_acc = Mock(cookies=cookies)
        wc = BaseWebClient(self.session)

        wc.user_request(mock_acc, 'http://example.com')

        self.session.cookies.update.assert_called_once_with(cookies)

    def test_user_request_updates_user_cookies(self):
        cookies = {'name': 'value'}
        mock_acc = Mock(cookies=None)
        self.session.cookies.get_dict = Mock(return_value=cookies)
        wc = BaseWebClient(self.session)
        wc.tracker_log_in = Mock(return_value=cookies)

        wc.user_request(mock_acc, 'http://example.com')

        self.assertIs(mock_acc.cookies, cookies)


class WebClientTestCase(URLFetchTestCase):

    def test_get_torrent_page_url_and_method(self):
        webclient = WebClient(self.session)
        webclient.get_torrent_page(1)
        self.session.request.assert_called_once_with('GET', 'http://rutracker.org/forum/viewtopic.php?t=1',
                                                     timeout=TIMEOUTS)

    def test_tracker_log_in_url_and_method(self):
        webclient = WebClient(self.session)
        mock_acc = Mock(username='user', password='password', userid=12345)

        webclient.tracker_log_in(mock_acc)
        formdata = WebClient.login_form_data(mock_acc)

        self.session.request.assert_called_once_with('POST',
                                                     'http://login.rutracker.org/forum/login.php',
                                                     data=formdata, timeout=TIMEOUTS)


class WebClientIntegrationTestCase(BetamaxTestCase):

    def test_get_torrent_page(self):
        webclient = WebClient(self.session)
        html = webclient.get_torrent_page(669606)
        self.assertIn(html, '669606')
