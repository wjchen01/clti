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
from canvastools.views import courseinfo
from urllib.parse import quote
from oauthlib.oauth1.rfc5849 import signature, errors

TOOLNAME = courseinfo.TOOLNAME
TCONFIG = util.CONFIG[TOOLNAME]
app.secret_key = os.urandom(24)

DEFAULTPIC = 'https://i1.wp.com/wjchensce.test.instructure.com/images/messages/avatar-50.png?ssl=1'

COURSE = {
    'canvas_id': 11080,
    'cid': 'SCNCC1000_001_2016_3',
    'title': 'FRONTIERS OF SCIENCE',
    'studentsNum': 573
    }

SCOURSE = {
    'Multi-TA': {
        'canvas_id': 9435,
	'cid': 'IEORE4004_001_2016_3',
        'title': 'OPTIMIZATION MODELS AND METHO',
        'time': 'Tu, Th 11:40am to 12:55pm',
        'location': 'RTBA',
        'Teacher': [
            {
                'id': '74034',
                'uni': 'sa3305',
                'email': 'sa3305@wjchen.org',
                'first': 'Shipra',
                'last': 'Agrawal'
                }
            ],
        'TA': [
            {
                'id': '43392',
                'uni': 'yj2379',
                'email': 'yj2379@wjchen.org',
                'first': 'Yingxiang',
                'last': 'Jiang'
                },
            {
                'id': '36092',
                'uni': 'fl2412',
                'email': 'fl2412@wjchen.org',
                'first': 'Fengpei',
                'last': 'Li'
                },
            {
                'id': '86326',
                'uni': 'nts2122',
                'email': 'n.sakr@wjchen.org',
                'first': 'Nouri',
                'last': 'Sakr'
                },
            {
                'id': '112906',
                'uni': 'rrs2169',
                'email': 'rrs2169@wjchen.org',
                'first': 'Roshni',
                'last': 'Shah'
                },
            {
                'id': '51308',
                'uni': 'rs3566',
                'email': 'r.singal@wjchen.org',
                'first': 'Raghav',
                'last': 'Singal',
                'pic': 'https://courseworks2.wjchen.org/images/thumbnails/715422/vkldXhKGcxKuBV7xFpQb4aBZrevdaCS8kJ1GwFse'
                }
            ]
        },
    'with-profile-pic': {
	'canvas_id': 6887,
        'cid': 'SOCWT660B_D33_2016_1',
        'title': 'HBSE-B: GENDER/SEXUALITY ONLI',
        'time': 'Th 7:00pm to 8:30pm',
        'location': 'RTBA',
        'Teacher': [
            {
                'id': '14908',
                'uni': 'ec3136',
                'email': 'ec3136@wjchen.org',
                'first': 'Elisabeth',
                'last': 'Counselman',
                'pic': 'https://courseworks2.wjchen.org/images/thumbnails/293851/eKw9tkUEgVr0Wn50F8vvWggDenKsqIh1u212tajf'
                }
            ],
        'TA': [
            {
                'id': '3076',
                'uni': 'ma3273',
                'email': 'ma3273@wjchen.org',
                'first': 'Malwina',
                'last': 'Andruczyk',
                'pic': 'https://online.ce.wjchen.org/images/thumbnails/91357/YQyLmzRORYXLfbRUkXMY8CJ90f9FcZSRQPJxjBh6'
                }
            ]
        },
    'with-location': {
        'canvas_id': 25201,
        'cid': 'WMSTG4000_001_2016_1',
        'title': 'SIGNIFICANT OTHERS',
        'time': 'M 2:10pm to 4:00pm',
        'location': 'SCHERMERHORN 754 EXT',
        'Teacher': [
            {
                'id': '27924',
                'uni': 'mk3586',
                'email': 'mk3586@wjchen.org',
                'first': 'Mana',
                'last': 'Kia'
                }
            ],
        'TA': []
        }
    }


VALIDPARAMS = {
    'oauth_consumer_key': TCONFIG['oauth_consumer_key'],
    'oauth_signature_method': 'HMAC-SHA1',
    'oauth_version': '1.0',
    'oauth_callback': 'about:blank',
    'lti_message_type': 'basic-lti-launch-request',
    'lti_version': 'lti-1.0',
    'custom_canvas_user_login_id': 'ag3811',
    'custom_canvas_user_id': '300486',
    'custom_canvas_course_id': COURSE['canvas_id'],
    'context_title': COURSE['title'],
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
    requri = 'https://localhost' + TCONFIG['launch_relative']
    uri = quote(requri, safe=b'~')
    base_string = 'POST&' + uri + '&' + quote(norm_params, safe=b'~')
    text_utf8 = base_string.encode('utf-8')
    key = quote(TCONFIG['oauth_consumer_secret'], safe=b'~') + '&'
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
        resp1 = self.app.post('/' + TOOLNAME + '/launch')
        self.assertEqual(resp1.status_code, 401)

    def test_oauth_no_timestamp(self):
        print('>> Test OAuth with no timestamp')
        resp2 = self.app.post(
            '/' + TOOLNAME + '/launch', data={
                'oauth_consumer_key': TCONFIG['oauth_consumer_key'],
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
        resp3 = self.app.post('/' + TOOLNAME + '/launch', data=params)
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
            '/' + TOOLNAME + '/launch',
            data=params2,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        resp5 = self.app.post(
            '/' + TOOLNAME + '/launch',
            data=params2,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' })
        self.assertEqual(resp5.status_code,401)

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
            '/' + TOOLNAME + '/launch',
            data=params3,
            environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' }
        )
        soup = BeautifulSoup(resp6.get_data(), 'html.parser')
        self.assertEqual(
            soup.select("#title")[0].get_text(),
            COURSE['title']
            )

    def test_time_loc_request(self):
        print('>> Test title, time and location')
        for status, course in SCOURSE.items():
            print(' > ' + status)
            params4 = copy.deepcopy(VALIDPARAMS)
            params4.update(
                {
                    'oauth_timestamp': str(int(time.time())),
                    'oauth_nonce': uuid.uuid1().hex,
                    'custom_canvas_course_id': course['canvas_id'],
                    'context_title': course['title'],
                    'lis_course_offering_sourcedid': course['cid'],
                    'launch_presentation_return_url':
                        util.CONFIG['app']['canvas_uri']\
                        + '/courses/' + str(course['canvas_id'])\
                        + '/external_content/success/external_tool_redirect'
                    }
                )
            params4['oauth_signature'] = getsig(params4)
            resp6 = self.app.post(
                '/' + TOOLNAME + '/launch',
                data=params4,
                environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' }
                )
            soup = BeautifulSoup(resp6.get_data(), 'html.parser')
            for var in ['title', 'time', 'location']:
                self.assertEqual(
                    soup.select("#" + var)[0].get_text(),
                    course[var]
                    )

    def test_instructors(self):
        print(">> Test instructors")
        for status, course in SCOURSE.items():
            print(' > ' + status)
            courseUrl = util.CONFIG['app']['canvas_uri']\
                + '/courses/' + str(course['canvas_id'])
            params4 = copy.deepcopy(VALIDPARAMS)
            params4.update(
                {
                    'oauth_timestamp': str(int(time.time())),
                    'oauth_nonce': uuid.uuid1().hex,
                    'custom_canvas_course_id': course['canvas_id'],
                    'context_title': course['title'],
                    'lis_course_offering_sourcedid': course['cid'],
                    'launch_presentation_return_url':
                        courseUrl\
                        + '/external_content/success/external_tool_redirect'
                    }
                )
            params4['oauth_signature'] = getsig(params4)
            resp6 = self.app.post(
                '/' + TOOLNAME + '/launch',
                data=params4,
                environ_base={'HTTP_X_FORWARDED_FOR': '127.0.0.1' }
                )
            soup = BeautifulSoup(resp6.get_data(), 'html.parser')
            for var in ['Teacher', 'TA']:
                for ind, inst in enumerate(course[var]):
                    ina = '{} {} ({})'.format(
                        course[var][ind]['first'],
                        course[var][ind]['last'],
                        var
                        )
                    nameid = "#" + var.lower() + str(ind)
                    picid = "#" + var.lower() + 'pic' + str(ind)

                    print(
                        soup.select("#" + var.lower() + 'pic' + str(ind))[0]
                        )
                    self.assertEqual(
                        soup.select(nameid)[0].get_text(),
                        ina
                        )
                    self.assertEqual(
                        soup.select(nameid)[0].find('a').attrs['href'],
                        'mailto:' + course[var][ind]['email']
                        )
                    self.assertEqual(
                        soup.select(picid)[0].find('a').attrs['href'],
                        courseUrl + '/users/' + course[var][ind]['id']
                        )

                    print(soup.select(picid)[0].find('img').attrs['src'])
                    if 'pic' in course[var][ind]:
                        self.assertEqual(
                            soup.select(picid)[0].find('img').attrs['src'],
                            course[var][ind]['pic']
                            )
                    else:
                        self.assertEqual(
                            soup.select(
                                picid
                                )[0].find('img').attrs['src'][-13:],
                            'avatar-50.png'
                            )
                            

    def tearDown(self):
        self.app = None
        pass



if __name__ == '__main__':
    unittest.main()
