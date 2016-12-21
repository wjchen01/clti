"""
Course Info Tool
"""
import logging
import time
import urllib
import uuid
from flask import Blueprint
from flask import render_template, request, abort, session, redirect
from lti import InvalidLTIRequestError
from requests_oauthlib import OAuth2Session
from oauthlib.oauth1 import InvalidRequestError
from ..common import util, auth

TOOLNAME = 'courseinfo'
TCONFIG = util.CONFIG[TOOLNAME]
COURSEINFO = Blueprint(TOOLNAME, __name__)
LOG = logging.getLogger(__name__)
SAKAIDBNAME = util.CONFIG['app']['sakaidb']
DBCONFIG = util.CONFIG[SAKAIDBNAME]


def authredir(approval_prompt='auto'):
    """
    Retrieve URL for authorization screen from auth.redir() and
    redirect browser to that URL
    """
    authurl, state = auth.redir(TOOLNAME, approval_prompt)
    session['oauth_state'] = state
    LOG.error("Redirecting for authorization")
    return redirect(authurl)

def token_saver(tokenresp):
    """
    Wraps the util.logtoken() function for use with requests_oauthlib
    """
    util.logtoken(tokenresp, TOOLNAME, session['custom_canvas_user_id'])


@COURSEINFO.route('/launch', methods=['GET', 'POST'])
def tool():
    """
    This checks for a valid LTI request from Canvas and stores
    relevant information in the session cookie.  If there is already a
    valid OAuth token, it creates a new OAuth2session object to
    connect to Canvas and calls rostermain() on it.  If there is no
    valid token, it calls authredir() for authentication and authorization.
    """
    try:
        if not auth.valid(TOOLNAME, request):
            LOG.error("Invalid request")
            abort(401)
    except (InvalidLTIRequestError, InvalidRequestError) as err:
        LOG.error("Invalid")
        LOG.error(err)
        abort(401)
    except AttributeError as err:
        LOG.error("courseinfo: missing " + str(err))
        abort(400)
    except ValueError as err:
        LOG.error("Exception in courseinfo()")
        LOG.error(err)
        abort(400)
    LOG.error('Request is valid')

    # save important values in session cookie
    session['uni'] = request.values['custom_canvas_user_login_id']
    session['custom_canvas_user_id'] = request.values['custom_canvas_user_id']
    session['custom_canvas_course_id']\
        = request.values['custom_canvas_course_id']
    session['tool'] = TOOLNAME
    session['context_title'] = request.values['context_title']

    session['id'] = session.get(id, uuid.uuid4().hex)
    LOG.error("Saved POST information")
    if 'lis_course_offering_sourcedid' in request.values:
        session['lis_course_offering_sourcedid']\
            = request.values['lis_course_offering_sourcedid']
    else:
        return render_template(
            "redirect.html",
            param={'error': 'No course specified!'}
            )

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
        cinfo = show_info(canvas)
        if not cinfo:
            return authredir('force')
        return cinfo
    else:
        return authredir()


@COURSEINFO.route('/info', methods=['GET'])
def show_info(canvas=None):
    """
    This retrieves information from the session cookie and creates an
    OAuth2session object if necesary.  It then retrieves the list of
    instructors from the Canvas API and the course meeting time and
    location from the database.

    Finally, it invokes the template and returns the page.
    """
    if not auth.sessiontoken(session):
        return authredir()
    param = {
        'title': session['context_title'],
        'server_uri': util.CONFIG['app']['canvas_uri'],
        'custom_canvas_course_id': session['custom_canvas_course_id'],
        'teachers': [],
        'tas': [],
        'loc': '',
        'maploc': '',
        'time': ''
        }

    if not canvas:
        canvas = auth.getsession(util.CONFIG['app']['devkey'], session['oauth_tokens'])

    (users, status) = util.canvasget(
        canvas,
        util.CONFIG['app']['canvas_uri'] + '/api/v1/courses/'\
            + session['custom_canvas_course_id']\
            + '/users?include[]=email&include[]=enrollments'\
            + '&include[]=avatar_url'\
            + '&enrollment_type[]=teacher&enrollment_type[]=ta'\
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

    for user in users:
        if user['enrollments'][0]['type'] == 'TaEnrollment':
            param['tas'].append(user)
        else:
            param['teachers'].append(user)

    conn = util.dbconnect(DBCONFIG)
    curr = conn.cursor()

    cinfoq = """ SELECT
    courseworks_doc_original_title, sis_meeting_location, sis_meeting_time
    FROM cu_course_site
    WHERE site_id = :site_id
    """
    queryparam = {'site_id': session['lis_course_offering_sourcedid']}
    results = curr.execute(cinfoq, queryparam).fetchall()
    LOG.debug(queryparam)
    LOG.debug(results)
    if curr.rowcount > 0:
        (param['title'], param['loc'], cotime) = results[0]
        wday = ', '.join(util.WEEKDAY[x] for x in cotime[0:7].strip())
        shour = str(int(cotime[7:9]))
        sampm = cotime[12:13].lower() + 'm'
        ehour = str(int(cotime[14:16]))
        param['time'] = wday + ' ' + shour + ':' + cotime[10:12] + sampm\
            + ' to '\
            + ehour + ':' + cotime[17:19] + cotime[19:20].lower() + 'm'

    curr.close()
    conn.close()

    return render_template('courseinfo.html', param=param)

@COURSEINFO.route('/mini/<cid>', methods=['GET'])
def embed_tool(cid):
    return "<h3>" + cid + "</h3>"

if __name__ == "__main__":
    print('This requires Flask and Blueprint')
