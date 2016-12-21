import unittest
import re
import html
from bs4 import BeautifulSoup
import sys
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from canvastools import app
from canvastools.views import researchguides

COURSES = {
    'ENGLC1010_901_2015_3': { 'DEPT': 'ENCL', 'SCHOOL': 'CCOL' },
    'FRENX3021_001_2016_3': { 'DEPT': 'FRNB', 'SCHOOL': 'BCOL' },
    'NECRPS5105_001_2016_3': { 'DEPT': 'DVSP', 'SCHOOL': 'SPEC' },
    'CHEMW1405_003_2011_1': { 'DEPT': 'CHEM', 'SCHOOL': 'INTF' },
    'MATHW4043_001_2014_3': { 'DEPT': 'MATH', 'SCHOOL': 'INTF' },
    'SOCWT6020_D41_2016_3': { 'DEPT': 'SOCW', 'SCHOOL': 'SSOC' }
}

RGURLHTTP = 'http://www.wjchen.org/cgi-bin/cul/rschloc?key='

class TestRgurl (unittest.TestCase):
    def setUp(self):
        pass

    def test_rgurl(self):
        for cid, course in COURSES.items():
            url = RGURLHTTP + cid + '&dept=' + course['DEPT'] + '&sch=' \
                + course['SCHOOL']
            self.assertEqual( researchguides.rgurl(cid)['url'], url)

class TestResearchGuides (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_frame(self):
        scriptpattern = '\\\\nwindow.open\("(.+?)", "_blank"\);\\\\n'

        for cid, course in COURSES.items():
            url = researchguides.rgurl(cid)['url']
            resp = self.app.post('/researchguides/launch', data={
                    'lis_course_offering_sourcedid': cid
                    }
                  )
            self.assertEqual(resp.status_code, 200)

            soup = BeautifulSoup(str(resp.get_data()), 'html.parser')
            self.assertEqual(
                url, soup.select("#linkA")[0].attrs['href']
                )

            match = re.search(scriptpattern, soup.select("#openScript")[0].text)
            self.assertTrue(match)
            self.assertEqual(url, html.unescape(match.group(1)))
 

if __name__ == '__main__':
    unittest.main()
