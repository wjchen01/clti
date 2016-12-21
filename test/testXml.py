import unittest
import lxml
from bs4 import BeautifulSoup
import sys
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from canvastools import app
from canvastools.common import util
from canvastools.views import roster


CONFIG = {
    'canvas_uri': 'https://wjchensce.test.instructure.com',
    'PREFERRED_URL_SCHEME': 'https',
    'tool_suffix': 'DEV'
    }

DBCONFIG = {
    'name': 'canvasdevdb01',
    'db': 'canvasdevdb01.cc.wjchen.org:1527/canvas1d.wjchen.org'
    }

TOOLCONFIG = {
    'name': 'roster',
    'title': 'Photo Roster',
    'launch_relative': '/roster/launch'
}

class TestXml (unittest.TestCase):
    def setUp(self):
        pass

    def test_config(self):
        for key, value in CONFIG.items():
            self.assertEqual( value, util.CONFIG['app'][key])

    def test_db(self):
        self.assertEqual(
            DBCONFIG['db'],
            util.CONFIG[DBCONFIG['name']]['cx']['db']
            )

    def test_tool(self):
        for key, value in TOOLCONFIG.items():
            if 'name' != key:
                self.assertEqual(
                    value,
                    util.CONFIG[TOOLCONFIG['name']][key]
                    )

class TestResearchGuides (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        resp = self.app.get('/roster.xml')
        self.assertEqual(resp.status_code, 200)
        soup = BeautifulSoup(str(bytes.decode(resp.get_data())), 'xml')
        self.assertEqual(
            TOOLCONFIG['title'],
            soup.cartridge_basiclti_link.title.string
            )
        self.assertEqual(
            TOOLCONFIG['title'] + ' ' + util.CONFIG['app']['tool_suffix'],
            soup.cartridge_basiclti_link.extensions.options.find('property', attrs={'name': 'text'}).string
            )

        self.assertEqual(
            util.CONFIG['app']['SERVER_NAME'] + TOOLCONFIG['launch_relative'],
            soup.cartridge_basiclti_link.secure_launch_url.string
            )

    def test_bad_request(self):
        resp = self.app.get('foo.xml')
        self.assertEqual(resp.status_code, 404)

if __name__ == '__main__':
    unittest.main()
