"""
Retrieve feed and build information from Jenkins, and display list of LTI tools
"""
import json
import logging
from datetime import datetime
from flask import Blueprint, Flask, current_app, Response, redirect
from flask import render_template, abort, session, jsonify, request
from xml.sax.saxutils import quoteattr
from jenkins import Jenkins, NotFoundException
from ..common import util, auth

TOOLNAME = 'admin'
ADMIN = Blueprint(TOOLNAME, __name__)

TCONFIG = util.CONFIG[TOOLNAME]
LOG = logging.getLogger(__name__)

CASURL = util.CONFIG['app']['CAS_SERVER'] + '/cas/login?TARGET='\
    + util.CONFIG['app']['SERVER_NAME'] + '/' + TOOLNAME + '/'
CAS2URL = util.CONFIG['app']['CAS_SERVER'] + '/cas/login?service='\
    + util.CONFIG['app']['SERVER_NAME'] + '/' + TOOLNAME + '/'


@ADMIN.route('/sub-account', methods=['GET', 'POST'])
def subaccount_move():
    """
    Move courses from one sub-account to another
    """
    if 'admin-uni' not in session:
        session['tlacasapp'] = 'sub-account'
        return redirect(CAS2URL)
    else:
        print("session['admin-uni'] = " + session['admin-uni'])
    param = {
        'uni': session['uni']
        }
    session['tlacasapp'] = None
    return render_template('samove.html', param=param)

@ADMIN.route('/', methods=['GET', 'POST'])
def admintool():
    """
    CAS routing for admin tools
    """
    if 'admin-uni' not in session:
        if 'ticket' in request.values:
            app = session['tlacasapp']
            session['tlacasapp'] = None
            uni = auth.cas(request.values['ticket'], TOOLNAME)
            if not uni:
                abort(401)
            session['admin-uni'] = uni
            return redirect(TOOLNAME + '/' + app)
    abort(404)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')

