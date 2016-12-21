import unittest
import sys
sys.path.insert(0, '{{ YOUR APP DIRECTORY }}')
from run import app
from canvastools.common import util

TESTVARS = 'YOUR TEST VARIABLES'

class TestTemplate (unittest.TestCase):
    def setUp(self):
        pass

    def test_1(self):
        # Put your test here. Make as many of these as you need
        self.assertEqual(2+2, 4)

class TestFlask (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_flask(self):
        resp = self.app.post('/' data={})
        self.assertEqual(resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()
