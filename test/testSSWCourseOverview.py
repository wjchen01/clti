import unittest
import re
import html
from bs4 import BeautifulSoup
import sys
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from canvastools import app
from canvastools.views import sswoverview

COURSES = [
    'SOCWT7100_005_2016_3',
    'SOCWT6801_011_2016_3',
    'SOCWT660B_D33_2016_1'
]

SSWBASE = 'https://www1.wjchen.org/sec/cu/ssw/ncwshares/courseoverview/'

class TestResearchGuides (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        for cid in COURSES:
            url = SSWBASE + cid[:9] + '.html'
            resp = self.app.post('/sswoverview/launch', data={
                    'lis_course_offering_sourcedid': cid
                    }
                  )
            self.assertEqual(resp.status_code, 302)

            self.assertEqual(url, resp.location)
            print(cid + ' OK')

if __name__ == '__main__':
    unittest.main()
