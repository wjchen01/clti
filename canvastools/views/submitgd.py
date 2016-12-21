"""
Includes LTI tool on canvas and interaction with SSOL.

"""
import datetime
import logging
import urllib
import uuid
import requests

from flask import Blueprint, request
from flask import session, abort, render_template
from ..common import util, auth

TOOLNAME = 'submitgd'
SUBMITGD = Blueprint(TOOLNAME, __name__)

LOG = logging.getLogger(__name__)

TCONFIG = util.CONFIG[TOOLNAME]
DBCONFIG = util.CONFIG[util.CONFIG['app']['dbserver']]
ACCESS_TOKEN =util.CONFIG['app']['access_token']

@SUBMITGD.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Step 1: The SSOL server passes a username and password to request
    a session ID
    '''
    users = TCONFIG['users']
    user_username = request.values['username']
    user_password = request.values['password']
    if user_password == users[user_username]['password']:
        # store current_user.id into session table
        ssolSession ={
            'id': uuid.uuid4().hex,
            'tool': TOOLNAME,
            'uni': 'SSOL',
            'lis_course_offering_sourcedid': 'SSOL'
            }
        util.logsession(ssolSession, request, TCONFIG['db_id'])
        return ssolSession['id']
    else:
        return 'Invalid User'

@SUBMITGD.route("/grades", methods=['POST'])
def grades():
    '''
    Step 2: Once the SSOL server has logged in, it can use its session
    ID to authenticate and send the course site ID.  This tool
    retrieves grades from Canvas for that site ID and returns them to
    the SSOL server as a comma-delimited string for import into the SIS
    database.
    '''
    status = ''
    xbox = []

    siteid = request.values['siteid']
    if 'sessionId' not in request.values:
        print("No session id Provided")
        abort(401)

    params = {
        'sessionId': request.values['sessionId']
        }
    con = util.dbconnect(DBCONFIG)
    curr = con.cursor()
    time = curr.execute(
        "SELECT session_start FROM sessions where SESSION_ID = :sessionId",
        params
        ).fetchone()
 
    if curr.rowcount < 1:
        print("Session id not found in database "+ request.values['sessionId'])
        abort(401)

    if (datetime.datetime.now() - time[0]).total_seconds() >= 60:
        abort(408)
        
    enrollurl = '/'.join(
        [
          util.CONFIG['app']['canvas_uri'],
          'api/v1/courses/sis_course_id:{}'.format(siteid),
          'enrollments/?per_page=100'
        ]
    )   
    headers={'Authorization': ACCESS_TOKEN}
    
    (xbox, status) = util.canvasget(requests, enrollurl, headers=headers)
    curr.close()
    con.close()

    if status != 200:
        LOG.error("Canvas status: " + str(status))
        abort(status)

    # need stores three-column-data
    # including 'Student Name','Student ID','Final_grade'
    need = []
    for i in range(0, len(xbox)):
        if 'grades' in xbox[i] and xbox[i]['grades']['final_grade'] != None:
            need.append([xbox[i]['user']['name'], \
                             xbox[i]['user']['login_id'], \
                             xbox[i]['grades']['final_grade']])
    string = [', '.join(str(c) for c in lst) for lst in need]
    string = '\n'.join(string)
    return string

@SUBMITGD.route("/launch", methods=['GET', 'POST'])
def submitgrades(name=None):
    '''
    LTI tool with explanation of grade submission process and link to
    SSOL server page
    '''
    return render_template('submitgrade.html', name=name, ssolurl=TCONFIG['ssolurl'])
