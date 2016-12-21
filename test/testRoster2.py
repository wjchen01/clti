import binascii
import copy
import hmac
import hashlib
import os
import time
import sys
import unittest
import uuid
SYSDIR = '/var/www/html/tlaservice-web/'
sys.path.insert(0, SYSDIR)
from bs4 import BeautifulSoup
from canvastools import app
from flask import Flask, Blueprint, Response
from canvastools.common import util
from canvastools.views import roster
from urllib.parse import quote
from oauthlib.oauth1.rfc5849 import signature, errors

CONFIG = util.CONFIG['roster']
app.secret_key = os.urandom(24)

COURSE = {
    'canvas_id': 11080,
    'cid': 'SCNCC1000_001_2016_3',
    'studentsNum': 573
    }

SCOURSE = {
    'CVN': {
        'canvas_id': 9435,
	'cid': 'IEORE4004_001_2016_3',
        'studentsNum': 93,
        'student': {
            'uni': 'cac2287',
            'first': 'Camilo',
            'last': 'Cardona Gomez'
            }
        },
    'NRA': {
	'canvas_id': 11650,
        'cid': 'JOURJ6910_001_2016_3',
        'studentsNum': 52,
        'student': {
            'uni': 'jcn2134',
            'first': 'Josephine',
            'last': 'Napolitano'
            }
        }
    }

STUDENT = {
    'uni': 'tcs2138',
    'first': 'Torrance',
    'last': 'Smith',
    'photosize': 25289,
    'canvas_id': 291947
    }

UNAUTH = 'tcs2134'

VALIDPARAMS = {
    'oauth_consumer_key': CONFIG['oauth_consumer_key'],
    'oauth_signature_method': 'HMAC-SHA1',
    'oauth_version': '1.0',
    'oauth_callback': 'about:blank',
    'lti_message_type': 'basic-lti-launch-request',
    'lti_version': 'lti-1.0',
    'custom_canvas_user_login_id': 'ag3811',
    'custom_canvas_user_id': '300486',
    'lis_course_offering_sourcedid': COURSE['cid'],
    'launch_presentation_return_url': util.CONFIG['app']['canvas_uri']\
        + '/courses/' + str(COURSE['canvas_id'])\
        + '/external_content/success/external_tool_redirect'
    }

def getsig(params1):
    nparams = []
    for key, value in params1.items():
        nparams.append(
            quote(key, safe=b'~') + '=' + quote(str(value), safe=b'~')
	    )
    nparams.sort()
    norm_params = '&'.join(nparams)
    requri = 'https://localhost' + CONFIG['launch_relative']
    uri = quote(requri, safe=b'~')
    base_string = 'POST&' + uri + '&' + quote(norm_params, safe=b'~')
    text_utf8 = base_string.encode('utf-8')
    key = quote(CONFIG['oauth_consumer_secret'], safe=b'~') + '&'
    key_utf8 = key.encode('utf-8')
    sig = hmac.new(key_utf8, text_utf8, hashlib.sha1)
    return binascii.b2a_base64(
        sig.digest()
	)[:-1].decode('utf-8')


class TestSecurity (unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_oauth1(self):
        print('>> Test OAuth with no POST data')
        resp1 = self.app.post('/roster/launch')
        self.assertEqual(resp1.status_code, 401)

    def test_oauth_no_timestamp(self):
        print('>> Test OAuth with no timestamp')
        resp2 = self.app.post(
            '/roster/launch', data={
                'oauth_consumer_key': CONFIG['oauth_consumer_key'],
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_signature': uuid.uuid1().hex
                }
            )
        self.assertEqual(resp2.status_code, 400)

    def test_oauth_bad_timestamp(self):
        print('>> Test OAuth with bad timestamp')
        params = copy.deepcopy(VALIDPARAMS)
        params.update(
            {
                'oauth_timestamp': int(time.time()) - 1000,
                'oauth_nonce': uuid.uuid1().hex
                }
            )
        params['oauth_signature'] = getsig(params)
        resp3 = self.app.post('/roster/launch', data=params)
        self.assertEqual(resp3.status_code, 401)

    def test_oauth_duplicate_nonce(self):
        print('>> Test OAuth with duplicate nonce')
        params2 = copy.deepcopy(VALIDPARAMS)
        params2.update(
            {
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': uuid.uuid1().hex,
                }
            )
        params2['oauth_signature'] = getsig(params2)
        resp4 = self.app.post(
            '/roster/launch',
            data=params2,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        resp5 = self.app.post(
            '/roster/launch',
            data=params2,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        self.assertEqual(resp5.status_code,401)

    def test_photo_auth(self):
        print('>> Test photo authorization')
        resp7 = self.app.get(
            '/roster/photo/' + UNAUTH + '.jpg'
            )
        self.assertEqual(resp7.status_code, 401)

    def test_oauth2_request(self):
        print('>> Test valid OAuth')
        params3 = copy.deepcopy(VALIDPARAMS)
        params3.update(
            {
                'oauth_timestamp': str(int(time.time())),
                'oauth_nonce': uuid.uuid1().hex,
                }
            )
        params3['oauth_signature'] = getsig(params3)
        resp6 = self.app.post(
            '/roster/launch',
            data=params3,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' }
        )
        soup = BeautifulSoup(resp6.get_data(), 'html.parser')
        self.assertEqual(
            int(soup.select("#studentsNum")[0].get_text()),
            COURSE['studentsNum']
            )
        print('>> Test photo grid for student name, uni, photo URL\
 and link to profile')
        # Check for existence of student photo and list entry
        purl = '/roster/photo/' + STUDENT['uni'] + '.jpg'
        profileurl = util.CONFIG['app']['canvas_uri'] + '/courses/' + str(
            COURSE['canvas_id']
            ) + '/users/' + str(STUDENT['canvas_id'])

        tagid = '_'.join([STUDENT['first'], STUDENT['last'], STUDENT['uni']])

        # TODO for photo check sortable_name
        self.assertEqual(
            soup.select('#photo_' + tagid)[0].contents[1].contents[3]\
                .contents[0].string.strip(),
            STUDENT['last'] + ', ' + STUDENT['first']		
            )
        # Is the profile url correct in the photo grid?
        self.assertEqual(
            profileurl, 
            soup.select('#lists_' + tagid)[0].contents[3].contents[0].get('href')
            )
        # Is the uni in the photo grid?
        self.assertEqual(
            soup.select(
                '#photo_' + tagid
                )[0].contents[1].contents[3].a.string,
            STUDENT['uni']
            )
	# Does the photo url show up?
        self.assertEqual(
            soup.select(
                '#photo_' + tagid
                )[0].contents[1].contents[1].contents[1].get('src'),
            util.CONFIG['app']['SERVER_NAME'] + purl
            )
        print('>> Test list view for student name, uni, photo URL\
 and link to profile')
        # Is the profile url correct in the list?
        self.assertEqual(
            profileurl, 
            soup.select(
                '#lists_' + tagid
                )[0].contents[3].contents[0].get('href')
            )
        # Is the uni in the list?
        self.assertEqual(
            soup.select(
                '#lists_' + tagid
                )[0].contents[3].contents[0].string.strip(),
            STUDENT['uni']
            )
        # Does the sortable name show up in the list?
        self.assertEqual(
            soup.select('#lists_' + tagid)[0].contents[1].string,
            STUDENT['last'] + ', ' + STUDENT['first']
            )
        # Can we read the photo?
        resp8 = self.app.get(purl)
        self.assertEqual(resp8.status_code, 200)
        # Is the photo the right size?
        self.assertEqual(len(resp8.get_data()),STUDENT['photosize'])


    def test_status_request(self):
        print('>> Test student status (NRA, CVN)')
        for status, course in SCOURSE.items():
            print(' > ' + status)
            params4 = copy.deepcopy(VALIDPARAMS)
            params4.update(
                {
                    'oauth_timestamp': str(int(time.time())),
                    'oauth_nonce': uuid.uuid1().hex,
                    'lis_course_offering_sourcedid': course['cid'],
                    'launch_presentation_return_url':
                        util.CONFIG['app']['canvas_uri']\
                        + '/courses/' + str(course['canvas_id'])\
                        + '/external_content/success/external_tool_redirect'
                    }
                )
            params4['oauth_signature'] = getsig(params4)
            resp6 = self.app.post(
                '/roster/launch',
                data=params4,
                environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' }
                )
            soup = BeautifulSoup(resp6.get_data(), 'html.parser')
            self.assertEqual(
		int(soup.select("#studentsNum")[0].get_text()),
	        course['studentsNum']
		)
            student = course['student']
            tagid = '_'.join(
                [student['first'], student['last'], student['uni']]
                ).replace(' ', '_')
            self.assertEqual(
		soup.select(
                    '#lists_' + tagid
                    )[0].contents[3].contents[0].string.strip(),
		student['uni']
		)
            self.assertEqual(
		soup.select(
                    '#lists_' + tagid
                    )[0].contents[5].string.strip(),
		status
		)


    def tearDown(self):
        self.app = None
        pass



if __name__ == '__main__':
    unittest.main()
