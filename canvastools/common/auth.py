"""
Common authentication functions for LTI tools
Angus Grieve-Smith for Columbia IT
"""
import time
import logging
import urllib
import cx_Oracle
from cas import CASClient
from requests_oauthlib import OAuth2Session
from oauthlib.oauth1 import InvalidRequestError
from oauthlib.oauth2.rfc6749.errors import MissingCodeError
from ..common import util
from .CWToolProvider import CWToolProvider
from .CWValidator import CWValidator

BASE_URI = util.CONFIG['app']['canvas_uri'] + '/login/oauth2/auth'
TOKEN_URI = util.CONFIG['app']['canvas_uri'] + '/login/oauth2/token'

LOG = logging.getLogger(__name__)

def callback(url, tool, state):
    """
    Function for common callback; this allows us to use one developer
    key for all tools
    """
    tconfig = util.CONFIG[tool]
    canvas = OAuth2Session(
        client_id=util.CONFIG['app']['devid'],
        state=state
        )
    try:
        tokenresp = canvas.fetch_token(
            TOKEN_URI,
            client_secret=util.CONFIG['app']['devkey'],
            authorization_response=url
            )
    except MissingCodeError:
        LOG.error("MissingCodeError in auth.callback()")
        raise
    return tokenresp, tconfig['main_route']

def cas(ticket, toolname, whitelist=None):
    """
    Verify CAS login and check affiliation if necessary
    """
    version='2'
    if whitelist:
        version='CAS_2_SAML_1_0'
        print("using SAML")
    cas = CASClient(
        version=version,
        service_url = util.CONFIG['app']['SERVER_NAME']+'/'+toolname+'/',
        server_url = util.CONFIG['app']['CAS_SERVER']
        )
    verif = cas.verify_ticket(ticket)
    print(verif)
    if whitelist and 'affiliation' in verif[1]\
            and verif[1]['affiliation'] == whitelist:
        return True
    else:
        return verif[0]

def sessiontoken(session):
    """
    Extract token information from the session cookie, or from the
    database if it is not in the session.  Update the session.
    """
    tconfig = util.CONFIG[session['tool']]
    if 'oauth_tokens' not in session\
            or 'access_token' not in session['oauth_tokens']\
            or len(session['oauth_tokens']['access_token']) < 1:
        LOG.error(
            "Getting token (" + str(tconfig['db_id']) + ', '\
 + str(session['custom_canvas_user_id']) + ')'
            )
        session['oauth_tokens'] = util.gettoken(
            tconfig['db_id'],
            session['custom_canvas_user_id']
            )
        if len(session['oauth_tokens']['access_token']) < 1:
            return False
        LOG.error("Got token")

    if float(util.CONFIG['app']['devkey_installed']) > \
            session['oauth_tokens']['expires_at']:
        LOG.error(
            "Dev key is newer than access token (%s > %s)",
            util.CONFIG['app']['devkey_installed'],
            round(session['oauth_tokens']['expires_at'])
            )
        return False
    else:
        expires_in = session['oauth_tokens']['expires_at'] - time.time()
        session['oauth_tokens']['expires_in'] = expires_in
        if expires_in < 0:
            LOG.error(
                "Token has expired! " + str(
                    session['oauth_tokens']['expires_at']
                    ) + ' - ' + str(time.time()) + ' = ' + str(expires_in))
    return True


def getsession(client_id, token):
    """
    Create an OAuth2 session for a client
    """
    return OAuth2Session(client_id=client_id, token=token)

def oauth_consumer_key(request):
    """
    Extract the tool name from the request URL and retrieve the tool
    key from the config file
    """
    return util.CONFIG[util.gettoolname(request)]['oauth_consumer_key']

def oauth_consumer_secret(request):
    """
    Extract the tool name from the request URL and retrieve the tool
    secret from the config file
    """
    return util.CONFIG[util.gettoolname(request)]['oauth_consumer_secret']

def redir(tool, approval_prompt='auto'):
    """
    Retrieves token or authorization url for tool
    """
    tconfig = util.CONFIG[tool]
    canvas = OAuth2Session(
        client_id=util.CONFIG['app']['devid'],
        redirect_uri=urllib.parse.urljoin(
            util.CONFIG['app']['SERVER_NAME'],
            'callback'
            )
        )

    authurl, state = canvas.authorization_url(
        BASE_URI,
        approval_prompt=approval_prompt
        )
    return authurl, state

def seentsn(params):
    """
    Checks to see if the timestamp and nonce have been seen before
    """
    seen = False
    tsnconfig = util.CONFIG[util.CONFIG['app']['dbserver']]
    tsnconn = util.dbconnect(tsnconfig)
    curr = tsnconn.cursor()
    selectq = """SELECT timestamp FROM NONCE
WHERE TIMESTAMP = :timestamp
AND NONCE = :nonce
"""
    LOG.debug(params)
    curr.execute(selectq, params).fetchall()
    if curr.rowcount > 0:
        LOG.debug('(' + params['timestamp'] + ', ' + params['nonce']\
                      + ') already seen!')
        seen = True
    insertq = """INSERT INTO NONCE (nonce, timestamp)
VALUES (:nonce, :timestamp)
"""
    try:
        curr.execute(insertq, params)
    except cx_Oracle.DatabaseError as err:
        LOG.error("Database error in logging nonce: %s", err)
    tsnconn.commit()
    curr.close()
    tsnconn.close()
    return seen

def valid(tool, request):
    """
    Checks to see if the request is valid OAuth1 from a Canvas server
    """
    tconfig = util.CONFIG[tool]
    try:
        provider = CWToolProvider.from_flask_request(
            secret=tconfig['oauth_consumer_secret'],
            request=request
            )
    except InvalidRequestError:
        raise
    validator = CWValidator()
    return provider.is_valid_request(validator)

def photoauth(toolid, uni, sessionid):
    """
    Checks to see whether a particular uni and session have been
    authorized to view a particular photo
    """
    fbpath = ''
    photoconn = util.dbconnect(util.CONFIG[util.CONFIG['app']['dbserver']])
    curr = photoconn.cursor()
    params = {
        'session_id': sessionid,
        'tool_id': toolid,
        'user_id': uni
        }
    LOG.info(params)
    photoq = """select path from photoauth where
session_id = :session_id and
tool_id = :tool_id and
user_id = :user_id
order by time desc
fetch next 1 row only
"""
    results = curr.execute(photoq, params).fetchone()
    if curr.rowcount > 0:
        fbpath = results[0]

    curr.close()
    photoconn.close()

    return fbpath
