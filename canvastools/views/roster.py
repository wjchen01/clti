"""
Flask module for photo roster

"""
from pathlib import Path
import logging
import time
import urllib
import uuid
from flask import Blueprint
from flask import abort, session, make_response
from flask import request, render_template, redirect, send_from_directory
from lti import InvalidLTIRequestError
from requests_oauthlib import OAuth2Session, TokenUpdated
from oauthlib.oauth1 import InvalidRequestError
from ..common import util, auth

TOOLNAME = 'roster'

ROSTER = Blueprint('roster', __name__)

TCONFIG = util.CONFIG[TOOLNAME]

LOGDIR = '/u/9/t/tltserv/log/'

LOG = logging.getLogger(__name__)

CANVAS_URI = util.CONFIG['app']['canvas_uri']
CANVAS_USER_PATH = '/api/v1/users/sis_user_id:'

SAKAIDBNAME = util.CONFIG['app']['sakaidb']
DBCONFIG = util.CONFIG[SAKAIDBNAME]

FBDEVPATH = '/facebook/facebook_dev/'
# FBDEVPATH = '/var/www/html/tlaservice-web/facebook_dev/'
FBPRODPATH = '/facebook/facebook_prod/'

def token_saver(tokenresp):
    """
    Wraps the util.logtoken() function for use with requests_oauthlib
    """
    util.logtoken(tokenresp, TOOLNAME, session['custom_canvas_user_id'])

@ROSTER.route("/photo/<uni>.jpg", methods=['GET'])
def facebook(uni):
    """
    Return photos for use in roster, after checking auth.photoauth()
    to make sure that they are authorized
    """
    LOG.debug("Facebook for " + uni)

    if 'id' not in session:
        abort(401)

    pfname = uni + '.jpg'
    fbpath = auth.photoauth(TCONFIG['db_id'], uni, session['id'])
    if len(fbpath) < 0:
        abort(401)

    if fbpath == util.CONFIG['static_folder']:
        pfname = 'crown.jpg'
    return send_from_directory(fbpath, pfname)


@ROSTER.route('/grid', methods=['GET', 'POST'])
def rostermain(canvas=None):
    """
    This retrieves information from the session cookie and creates an
    OAuth2session object if necesary.  It then retrieves the list of
    students and groups from the Canvas API and any CVN or NRA users
    from the database.  It generates the photo URL for each student
    depending on where the user photo is stored.  Finally, it invokes
    the template and returns the page.
    """
    LOG.error("Main roster")
    lprl = ''
    status = ''

    if not canvas:
        canvas = auth.getsession(
            util.CONFIG['app']['devkey'],
            session['oauth_tokens']
            )
    if 'lis_course_offering_sourcedid' in session\
            and 'launch_presentation_return_url' in session:
        lprl = session['launch_presentation_return_url']
        cid = session['lis_course_offering_sourcedid']
    elif 'lis_course_offering_sourcedid' in request.values:
        lprl = request.values['launch_presentation_return_url']
        cid = request.values['lis_course_offering_sourcedid']
    else:
        return render_template(
            'redirect.html',
            param={'error': 'No course specified'}
            )
    param = {
        'photourl': urllib.parse.urljoin(
            util.CONFIG['app']['SERVER_NAME'],
            TOOLNAME + '/' + 'photo'
            ),
        'canvas_course_id': util.canvas_course_id(lprl),
        'cid': cid,
        'uni': session['uni'],
        'jstest': False,
        'role': [],
        'users': []
        }
    param['jstest'] = util.CONFIG['app']['tool_suffix'] == 'DEV'

    util.logsession(session, request, TCONFIG['db_id'])

    (users, status) = util.canvasget(
        canvas,
        CANVAS_URI + '/api/v1/courses/' + param['canvas_course_id']\
            + '/users?include[]=email&enrollment_type=student'\
            + '&per_page=600'
        )
    
    if not users:
        if status == 'Not found':
            return render_template(
                'redirect.html',
                param={'info': 'No students found'}
                )
        LOG.error("Error getting users: " + status)
        return authredir()
    LOG.error("Got users")

    # Check for NRAs, LRAs and CVNs in database
    conn = util.dbconnect(DBCONFIG)
    curr = conn.cursor()

    roleq = """SELECT eid, status
FROM sakai_user_id_map su LEFT JOIN CU_REALM_RL_GR realm 
ON su.user_id=realm.user_id
WHERE realm.realm_id = :realm_id
"""
    queryparam = { 'realm_id': '/site/' + param['cid'] }
    results = curr.execute(roleq, queryparam).fetchall()
    if curr.rowcount > 0:
        param['role'] = dict(results)

    curr.close()
    conn.close()


    (groups, status) = util.canvasget(
        canvas,
        CANVAS_URI + '/api/v1/courses/' + param['canvas_course_id'] + '/groups'
        )
    LOG.error("Got list of groups")
    grouplist = {}
    if status == 'OK':
        for group in groups:
            groupusers = []
            groupsimple = []
            (groupusers, status) = util.canvasget(
                canvas,
                CANVAS_URI + '/api/v1/groups/' + str(group['id']) + '/users'
                )
            for gusers in groupusers:
                groupsimple.append(gusers['sis_user_id'])
                grouplist.update(
                    {
                        group['id']: {
                            'name': group['name'],
                            'members': groupsimple
                            }
                        }
                    )
            LOG.error("Got group " + group['name'])
    param['groups'] = grouplist
    param['server_uri'] = CANVAS_URI
    LOG.error("Now logging users")

    for duser in users:
        if 'sis_user_id' not in duser:
            LOG.error ('sis_user_id not in user ' + duser['name'])
            duser['sis_user_id'] = str(duser['id'])
        uni = duser['sis_user_id']
        devpath = FBDEVPATH + uni[0:1] + '/' + uni[1:2] + '/'
        prodpath = FBPRODPATH + uni[0:1] + '/' + uni[1:2] + '/'
        if util.CONFIG['app']['tool_suffix'] == 'DEV'\
 and Path(devpath, uni + '.jpg').is_file():
            duser['fbpath'] = devpath
        elif Path(prodpath, uni + '.jpg').is_file():
            duser['fbpath'] = prodpath
        else:
            duser['fbpath'] = util.CONFIG['static_folder']
        param['users'].append(duser)

    util.logusers(session['id'], TCONFIG['db_id'], param['users'])
    LOG.error("Done logging users")

    """
    "Compact privacy policy" hack to use cookies in Iframes on
    Internet Explorer
    
    http://stackoverflow.com/questions/389456/cookie-blocked-not-saved-in-iframe-in-internet-explorer
    
    """
    page = render_template('roster.html', param=param)
    response = make_response(page)
    response.headers['P3P'] = 'CP="Potato"'

    LOG.error("Returning page")
    return response


@ROSTER.route('/launch', methods=['GET', 'POST'])
def photoroster():
    """
    This checks for a valid LTI request from Canvas and stores
    relevant information in the session cookie.  If there is already a
    valid OAuth token, it creates a new OAuth2session object to
    connect to Canvas and calls rostermain() on it.  If there is no
    valid token, it calls authredir() for authentication and authorization.
    """
    LOG.error("Photo roster launched")
    try:
        if not auth.valid(TOOLNAME, request):
            LOG.error("Invalid request")
            abort(401)
    except (InvalidLTIRequestError, InvalidRequestError) as err:
        LOG.error("Invalid")
        LOG.error(err)
        abort(401)
    except AttributeError as err:
        LOG.error("photoroster: missing " + str(err))
        abort(400)
    except ValueError as err:
        LOG.error("Exception in photoroster()")
        LOG.error(err)
        abort(400)
    LOG.error('Request is valid')

    # save important values in session cookie
    session['uni'] = request.values['custom_canvas_user_login_id']
    session['custom_canvas_user_id'] = request.values['custom_canvas_user_id']
    session['tool'] = TOOLNAME
    if 'id' not in session:
        session['id'] = uuid.uuid4().hex
    if 'lis_course_offering_sourcedid' in request.values:
        session['lis_course_offering_sourcedid']\
            = request.values['lis_course_offering_sourcedid']
    elif 'context_label' in request.values:
        session['lis_course_offering_sourcedid']\
            = request.values['context_label']
    else:
        return render_template(
            "redirect.html",
            param={'error': 'No course specified!'}
            )

    session['launch_presentation_return_url']\
        = request.values['launch_presentation_return_url']

    if auth.sessiontoken(session):
        canvas = OAuth2Session(
            util.CONFIG['app']['devid'],
            token=session['oauth_tokens'],
            auto_refresh_url=auth.TOKEN_URI,
            auto_refresh_kwargs={
                'client_id': util.CONFIG['app']['devid'],
                'client_secret': util.CONFIG['app']['devkey']
                },
            redirect_uri=urllib.parse.urljoin(
                util.CONFIG['app']['SERVER_NAME'],
                'callback'
                ),
            token_updater=token_saver
            )
        roster = rostermain(canvas)
        if not roster:
            return authredir('force')
        return roster
    else:
        return authredir()


def authredir(approval_prompt='auto'):
    """
    Retrieve URL for authorization screen from auth.redir() and
    redirect browser to that URL
    """
    authurl, state = auth.redir(TOOLNAME, approval_prompt)
    session['oauth_state'] = state
    LOG.error("Redirecting for authorization")
    return redirect(authurl)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')
