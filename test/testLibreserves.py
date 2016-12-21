import unittest
import re
import html
from bs4 import BeautifulSoup
import sys
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from canvastools import app
from canvastools.views import libreserves

STATICRESERVES = "https://courseworks.wjchen.org/reserves/"
ACTIVERESERVES = 'https://www1.wjchen.org/sec-cgi-bin/cul/respac/respac?'

ROLE = {
    'student': 'urn:lti:instrole:ims/lis/Student',
    'instructor': 'urn:lti:instrole:ims/lis/Instructor'
}

COURSE = {
    'active': {
        'hasreserves': 'CHEMW1403_002_2016_3',
        'noreserves': 'FRENX3006_003_2016_3'
        },
    'inactive': {
        'hasreserves': 'ARCHA4402_001_2016_2',
        'noreserves': 'ARCHA4488_001_2016_2'
        }
}

RESERVEURL = {
    'inactive': COURSE['inactive']['hasreserves'][-6:]\
        + '/' + COURSE['inactive']['hasreserves'] + '-reserves.shtml',
    'active': 'CRSE=20163CHEM1403W002'
}

NEWWINDOW = {
        'cid': COURSE['active']['noreserves'],
        'ext_roles': 'instructor',
        'url': 'http://library.wjchen.org/find/reserves.html'
        }

MESSAGE = {
    'wereno': {
        'cid': COURSE['inactive']['noreserves'],
        'ext_roles': 'student',
        'content': "There were no reserves for the course "\
            + COURSE['inactive']['noreserves'] + '.'
        },
    'notsetup': {
        'cid': COURSE['active']['noreserves'],
        'ext_roles': 'student',
        'content': 'Reserves for the course '\
            + COURSE['active']['noreserves']\
            + ' have not been set up.'
        }
}

IFRAME = {
    'archivelink': {
        'cid': COURSE['inactive']['hasreserves'],
        'ext_roles': 'student',
        'url': STATICRESERVES + RESERVEURL['inactive']
        },
    'activelink': {
        'cid': COURSE['active']['hasreserves'],
        'ext_roles': 'student',
        'url': ACTIVERESERVES + RESERVEURL['active']
        }
}

class TestMessage (unittest.TestCase):
    def setUp(self):
        pass

    def test_lrparam(self):
        for scenario in MESSAGE.values():
            self.assertEqual(
                libreserves.lrparam(scenario['cid'],
                          scenario['ext_roles']
                          )['info'],
                scenario['content']
                )

class TestIframe (unittest.TestCase):
    def setUp(self):
        pass

    def test_lrparam(self):
        for scenario in IFRAME.values():
            self.assertEqual(
                libreserves.lrparam(
                    scenario['cid'],
                    ROLE[scenario['ext_roles']]
                    )['url'],
                scenario['url']
                )
class TestNewWindow (unittest.TestCase):
    def setUp(self):
        pass

    def test_lrparam(self):
        self.assertEqual(
            libreserves.lrparam(
                NEWWINDOW['cid'],
                ROLE[NEWWINDOW['ext_roles']]
                )['url'],
            NEWWINDOW['url']
            )

class TestMessageFrame (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        for scenario in MESSAGE.values():
            resp = self.app.post('/libreserves/launch', data={
                    'lis_course_offering_sourcedid': scenario['cid'],
                    'ext_roles': ROLE[scenario['ext_roles']]
                    }
                  )
            self.assertEqual(resp.status_code, 200)

            soup = BeautifulSoup(str(resp.get_data()), 'html.parser')
            self.assertEqual(
                scenario['content'], soup.select("#info")[0].text.strip()
                )

class TestIframeFrame (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        refreshpattern = "0; url=\\\\'(.+?)\\\\'"

        for scenario in IFRAME.values():
            resp = self.app.post('/libreserves/launch', data={
                    'lis_course_offering_sourcedid': scenario['cid'],
                    'ext_roles': ROLE[scenario['ext_roles']]
                    }
                  )
            self.assertEqual(resp.status_code, 302)

            self.assertEqual(scenario['url'], resp.location)
            """
            soup = BeautifulSoup(str(resp.get_data()), 'html.parser')
            self.assertEqual(
                scenario['url'], soup.select("#linkA")[0].attrs['href']
                )

            match = re.search(
                refreshpattern,
                soup.select("#refreshMeta")[0].attrs['content']
                )
            self.assertEqual(
                scenario['url'], html.unescape(match.group(1))
                )
            """

class TestNewwindowFrame (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        scriptpattern = '\\\\nwindow.open\("(.+?)", "_blank"\);\\\\n'
        resp = self.app.post('/libreserves/launch', data={
                'lis_course_offering_sourcedid': NEWWINDOW['cid'],
                'ext_roles': ROLE[NEWWINDOW['ext_roles']]
                }
                             )
        self.assertEqual(resp.status_code, 200)

        soup = BeautifulSoup(str(resp.get_data()), 'html.parser')
        self.assertEqual(
            NEWWINDOW['url'], soup.select("#linkA")[0].attrs['href']
            )
        match = re.search(scriptpattern, soup.select("#openScript")[0].text)
        self.assertTrue(match)
        self.assertEqual(NEWWINDOW['url'], html.unescape(match.group(1)))

if __name__ == '__main__':
    unittest.main()
