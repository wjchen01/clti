"""
Common utilities used by LTI tools
Angus Grieve-Smith for Columbia University IT
"""
from pathlib import Path
import re
import json
import logging
import socket
import time
import urllib
import cx_Oracle
from lti import ToolConfig
from flask import Flask
from oauthlib.oauth2 import InvalidClientError, InvalidClientIdError

CONFIG = {}

APP = Flask(__name__)

LOG = logging.getLogger(__name__)

COURSERE = re.compile('/courses/(.+?)/')

SEMESTERNUM = {
    'Spring': 1,
    'Summer': 2,
    'Fall': 3
}

WEEKDAY = {
    'M':'M', 'T':'Tu', 'W':'W', 'R':'Th', 'F':'F', 'S':'Sa', 'U':'Su',' ':''
}

NSMAP = {
    'blti': 'http://www.imsglobal.org/xsd/imsbasiclti_v1p0',
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'lticp': 'http://www.imsglobal.org/xsd/imslticp_v1p0',
    'lticm': 'http://www.imsglobal.org/xsd/imslticm_v1p0',
    }

ENROLLMENTS = {
    "StudentEnrollment": "Student",
    "TeacherEnrollment": "Instructor",
    "TaEnrollment": "Teaching Assistant",
    "DesignerEnrollment": "Course Designer",
    "ObserverEnrollment": "Observer"
    }

JENKINSSTATUS = {
    "SUCCESS": {
        'strap': 'primary',
        'color': 'blue'
        },
    "UNSTABLE": {
        'strap': 'warning',
        'color': 'yellow'
        },
    "None": {
        'strap': 'info',
        'color': 'red_anime'
        },
    "FAILURE": {
        'strap': 'danger',
        'color': 'red'
        }
}

REGEX = {
    'parens': re.compile(r'\s*\(|\[.+?\)|\]\s*'),
    'and': re.compile(r'\s*\S+\&\s*'),
    'single': re.compile(r'\b\S\b'),
    'num': re.compile(r'\s+\w*\d+\w*( EXT)?$'),
    'seeley': re.compile('SEELEY W\. MUDD'),
    'iab': re.compile('INTERNATIONAL AFFAIRS BUILDING'),
    'brh': re.compile('Broadway Residence Hall')
}

CITYSTATEZIP = 'New York, NY 10027'

def loadconfig():
    """
    Load configuration from json files
    """
    CONFIG['static_folder'] = str(Path(Path(APP.root_path).parent, 'static'))

    for cfile in Path(APP.instance_path).iterdir():
        if cfile.name[-5:] == '.json' and cfile.name != 'config.json':
            name = cfile.name[:-5]
            LOG.debug("Loading " + name)
            with cfile.open() as json_data_file:
                CONFIG[name] = json.load(json_data_file)

loadconfig()

def https(url):
    """
    Convert url from HTTP to HTTPS
    """
    if url[:8] == 'https://':
        return url
    if url[:7] != 'http://':
        return False
    return 'https://' + url[7:]

def gettoolname(request):
    """
    Parse request URI and extract tool name
    """
    uri = ''
    if request.uri:
        uri = request.uri
    else:
        uri = request.url
    return urllib.parse.urlparse(uri).path.split('/')[1]

def lticonfig(tool):
    """
    Generate LTI XML from local configuration
    """
    if tool not in CONFIG:
        return False
    else:
        tconfig = CONFIG[tool]

    if 'title' not in tconfig:
        return False
    else:
        text = tconfig['title']

    if 'launch_relative' in tconfig:
        launch = CONFIG['app']['SERVER_NAME'] + tconfig['launch_relative']
    elif 'launch_uri' in tconfig:
        launch = tconfig['launch_url']
    else:
        return False

    if 'icon_relative' in tconfig:
        icon = CONFIG['app']['SERVER_NAME'] + tconfig['icon_relative']
    elif 'icon_uri' in tconfig:
        icon = tconfig['icon_url']
    else:
        icon = ''

    if 'tool_suffix' in CONFIG['app']:
        text += ' ' + CONFIG['app']['tool_suffix']

    outconfig = ToolConfig(
        launch_url=launch,
        secure_launch_url=launch,
        title=tconfig['title'],
        extensions={
            'canvas.instructure.com': {
                'tool_id':'cu_' + tool,
                'privacy_level':'public',
                'course_navigation': {
                    'url': launch,
                    'text': text,
                    'visibility': tconfig['visibility'],
                    'enabled': 'true',
                    'default': 'enabled'
                    }
                }
            },
        icon=icon,
        description=tconfig['description'],
        cartridge_bundle='BLTI001_Bundle',
        cartridge_icon='BLTI001_icon'
        )
    outxml = outconfig.to_xml().decode("utf-8")
    if len(outxml) < 40:
        outxml = outxml + '<error>Error creating XML</error>'
    return outxml

def dbconnect(dbconfig):
    """
    Connect to database
    """
    return cx_Oracle.connect(
        dbconfig['cx']['user'],
        dbconfig['cx']['passwd'],
        dbconfig['cx']['db']
        )

def canvasget(canvas, url, headers=None):
    """
    Send an API call to the Canvas server, handling pagination and
    token errors
    """
    results = []
    status = "OK"
    try:
        if headers:
            response = canvas.get(url, headers=headers)
        else:
            response = canvas.get(url)
    except (InvalidClientError, InvalidClientIdError) as err:
        LOG.error(err)
        return False, err.description
    if 'link' not in response.headers:
        if 'errors' in response.json():
            return False, response.json()['errors'][0]['message']
        LOG.error("No link header found!")
        status = response.status_code
        url = None
    else:
        results.extend(response.json())
        while "next" in response.links:
            if headers:
                response = canvas.get(
                    response.links['next']['url'],
                    headers=headers
                    )
            else:
                response = canvas.get(response.links['next']['url'])

            results.extend(response.json())
    if status == 'OK' and len(results) < 1:
        status = 'Not found'
    return results, status

def logtoken(tokenresp, toolname, user_id):
    """
    Log access and refresh tokens received
    """
    tconn = dbconnect(CONFIG[CONFIG['app']['dbserver']])
    tcurr = tconn.cursor()
    params = {
        'tool_id': CONFIG[toolname]['db_id'],
        'access_token': tokenresp['access_token'],
        'refresh_token': tokenresp['refresh_token'],
        'expires_in': tokenresp['expires_in'],
        'expires_at': tokenresp['expires_at'],
        'token_type': tokenresp['token_type'],
        'user_name': tokenresp['user']['name'],
        'user_id': user_id
        }
    tokenuq = """update tokens
set access_token = :access_token,
  refresh_token = :refresh_token,
  expires_in = :expires_in,
  expires_at = :expires_at,
  token_type = :token_type,
  user_name = :user_name,
  issued = CURRENT_TIMESTAMP
where user_id = :user_id
  and tool_id = :tool_id
"""
    try:
        tcurr.execute(tokenuq, params)
    except cx_Oracle.DatabaseError as err:
        LOG.error("Database error in logging tokens (update): %s", err)

    if tcurr.rowcount < 1:
        tokenq = """insert into tokens (
tool_id, access_token, refresh_token, expires_in, expires_at,
token_type, user_name, user_id, issued
) values (
:tool_id, :access_token, :refresh_token, :expires_in, :expires_at,
:token_type, :user_name, :user_id, CURRENT_TIMESTAMP
)
"""
        try:
            tcurr.execute(tokenq, params)
        except cx_Oracle.DatabaseError as err:
            LOG.error("Database error in logging tokens (new insert): %s", err)

        tconn.commit()
        LOG.error("Logged tokens (new insert)")
    else:
        tconn.commit()
        LOG.error("Logged tokens (update)")

    tcurr.close()
    tconn.close()

def gettoken(tool_id, user_id):
    """
    Look in database for oauth token
    """
    oauth_tokens = {
        'access_token': '',
        'user': {
            'id': user_id
            }
        }
    params = {
        'user_id': user_id
        }
    tokenq = """select
access_token, refresh_token, expires_at, token_type, expires_in, user_name
from tokens
where user_id = :user_id
order by expires_at desc
"""
    tconn = dbconnect(CONFIG[CONFIG['app']['dbserver']])
    tcurr = tconn.cursor()
    try:
        results = tcurr.execute(tokenq, params).fetchone()
    except cx_Oracle.DatabaseError as err:
        LOG.error("Database error in retrieving tokens: %s", err)

    if tcurr.rowcount > 0:
        oauth_tokens = {
            'access_token': results[0],
            'refresh_token': results[1],
            'expires_at': results[2],
            'token_type': results[3],
            'expires_in': results[4],
            'user': {
                'name': results[5],
                'id': user_id
                }
            }
    else:
        LOG.error("no token found for " + str(tool_id) + ', ' + user_id)
    tcurr.close()
    tconn.close()
    return oauth_tokens

def logusers(sessionid, toolid, users):
    """
    Log a record of all users
    """
    uconfig = CONFIG[CONFIG['app']['dbserver']]
    uconn = dbconnect(uconfig)
    ucurr = uconn.cursor()
    useruq = """update photoauth
set time = CURRENT_TIMESTAMP,
  role = :role,
  avatar_url = :avatar_url,
  path = :path
where session_id = :session_id
  and tool_id = :tool_id
  and user_id = :user_id
"""

    userq = """insert into photoauth (
session_id, tool_id, user_id, role, avatar_url, path, time
) values (
:session_id, :tool_id, :user_id, :role, :avatar_url, :path, CURRENT_TIMESTAMP
)
"""
    for user in users:
        avatar_url = ''
        role = ''
        if 'avatar_url' in user:
            avatar_url = user['avatar_url']
        if 'enrollments' in user:
            role = user['enrollments'][0]['role']
        params = {
            'session_id': sessionid,
            'tool_id': toolid,
            'user_id': user['sis_user_id'],
            'role': role,
            'avatar_url': avatar_url,
            'path': user['fbpath']
            }
        res = ucurr.execute(useruq, params)
        if ucurr.rowcount < 1:
            try:
                ucurr.execute(userq, params)
            except cx_Oracle.DatabaseError as err:
                LOG.debug(
                    "Database error in logging students (insert): %s", err
                    )

    uconn.commit()
    ucurr.close()
    uconn.close()

def logsession(session, request, toolid):
    """
    Save session information in the database
    """
    sessionconfig = CONFIG[CONFIG['app']['dbserver']]
    sessionconn = dbconnect(sessionconfig)
    sessioncurr = sessionconn.cursor()
    params = {
        'session_id': session['id'],
        'session_server': socket.gethostname(),
        'session_user': session['uni'],
        'session_ip': request.environ['HTTP_X_FORWARDED_FOR'],
        'session_user_agent': request.user_agent.string
        }
    LOG.error("Log session:")
    sessionuq = """update sessions
set session_server = :session_server,
  session_user = :session_user,
  session_ip = :session_ip,
  session_user_agent = :session_user_agent,
  session_active = 1
where session_id = :session_id
"""
    res = sessioncurr.execute(sessionuq, params)
    if sessioncurr.rowcount < 1:
        sessionq = """insert into sessions (
session_id, session_server, session_user, session_ip, session_user_agent,
session_start, session_active
) values (
:session_id, :session_server, :session_user, :session_ip, :session_user_agent,
CURRENT_TIMESTAMP, 1
)
"""
        try:
            sessioncurr.execute(sessionq, params)
        except cx_Oracle.DatabaseError as err:
            LOG.error("Database error in logging sessions: %s", err)
        LOG.error("Logged session (insert)")
    else:
        LOG.error("Logged session (update)")

    params = {
        'tool_id': toolid,
        'site_id': session['lis_course_offering_sourcedid'],
        'session_id': session['id']
        }
    toolq = """insert into lti_tool_access (
tool_id, site_id, session_id, visited_on
) values (
:tool_id, :site_id, :session_id, CURRENT_TIMESTAMP
)
"""
    try:
        sessioncurr.execute(toolq, params)
    except cx_Oracle.DatabaseError as err:
        LOG.error("Database error logging tool access: %s", err)
    sessionconn.commit()

    sessioncurr.close()
    sessionconn.close()

def current_semester(cur):
    """
    Retrieve the current semester from the database
    """
    query = """SELECT VALUE
FROM SAKAI_USER_PROPERTY
WHERE USER_ID = 'de1a9ecb-7527-43bc-b7d6-9d17661ac0fc'
AND NAME = 'wjchen.current.semester'
"""
    results = cur.execute(query).fetchone()
    return SEMESTERNUM[results[0].read().split(' ')[0]]

def canvas_course_id(url):
    """
    Extract Canvas course ID number from referring URL
    """
    cid = ''
    match = COURSERE.search(url)
    if match:
        cid = match.group(1)
    return cid

def maploc(loc):
    """
    Converts Registrar-style building locations to Google
    Maps-friendly addresses.

    Procedure used by Web team for Vergil:

    * Remove anything within parenthesis or brackets
    * Remove ampersand and anything before it
    * Remove numbers from addresses
    * Remove single characters (usually residuals from removing address numbers)
    * Remove names Google does not register

    """


    loc = REGEX['parens'].sub('', loc)
    loc = REGEX['and'].sub('', loc)
    loc = REGEX['num'].sub('', loc)

    """
    'parens'    'and'    'single'    'num'    'seeley'    'iab'    'brh'
    """
    """
    /* For non-street address, strip room numbers */
    if (!location.match(' Ave')) {
      location = location.replace(/LL[0-9]/g, '').replace(/[0-9]/g, '');
    }
    /* Some text substitutions */
    location = location.replace('Seeley W.', '').replace('International Affairs Building', '420 W 118th St').replace('Broadway Residence Hall', '2900 Broadway');

    """
    return loc + ', New York, NY 10027'
