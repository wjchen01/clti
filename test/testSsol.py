import os
import sys
import unittest
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from canvastools import app
from flask import Flask, Blueprint, Response
from canvastools.common import util
from canvastools.views import submitgd

class SsolFlaskTestCase(unittest.TestCase):
    #sets data dictionary
    data = {'username':'ssolreader','password':'23hrp8ddvnq394tuh90'}
        
    # Ensures that SSOL Grades Page is working
    def test_index_of_ssol_page(self):
        print(self.data)
        tester = app.test_client(self)
        response = tester.get('/submit/launch', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    # Verifies login page accepts valid user sends session id, rejects non valid
    def test_verify_login_works(self):
        tester = app.test_client(self)
        response = tester.post('/submit/login', data=self.data,
        environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })

    # Verifies that login works,login session key works, and data is received.
    def test_data_is_received(self):
        tester = app.test_client(self)
        response = tester.post('/submit/login', data=self.data,
        environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        print(response.data.decode() + '\x1b[6;30;42m' + 'RESPONSE DATA ' + '\x1b[0m')
        data = {'siteid':'TEST90001_001_20121','sessionId':'NONE'}
        data['sessionId'] = response.data.decode()
        response = tester.post('/submit/grades', data=data, environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.data, None)

if __name__ == '__main__':
    unittest.main()

