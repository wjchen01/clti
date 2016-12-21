"""
Flask module for miscellaneous server routes

"""
import logging
from flask import Blueprint, Response
from flask import abort, session, request, redirect, render_template
from oauthlib.oauth2.rfc6749.errors import MissingCodeError
from ..common import util, auth

MISC = Blueprint('misc', __name__)

LOG = logging.getLogger(__name__)

@MISC.route('/callback', methods=['GET'])
def callback():
    """
    Central callback route for all OAuth2 requests
    """
    tool = session['tool']
    try:
        tokenresp, main_route = auth.callback(
            util.https(request.url),
            tool,
            session['oauth_state']
            )
    except MissingCodeError:
        LOG.error("MissingCodeError in misc")
        return render_template(
            "redirect.html", param={
                'info': 'This tool will not function unless authorized.\
  To use it, please refresh the page and click "Authorize."'
                }
            )
    session['oauth_tokens'] = tokenresp
    util.logtoken(
        tokenresp,
        tool,
        session['custom_canvas_user_id']
        )
    return redirect('/'.join([util.CONFIG['app']['SERVER_NAME'], tool, main_route]))

@MISC.route('/casback', methods=['GET'])
def casback():
    """
    """
    if 'uni' not in session:
        if 'ticket' not in request.values:
            session['tlacasapp'] = 'tools'
            return redirect(CASURL)
        else:
            uni = auth.cas(request.values['ticket'], TOOLNAME, 'tlastaff')
            if not uni:
                abort(401)
            session['uni'] = uni
    if 'tlacasapp' in session:
        return redirect('/dash/' + session['tlascasapp'])

@MISC.route("/health")
def health_check():
    """
    Confirmation message for health check
    """
    return "service is running"

@MISC.route('/<tool>.xml', methods=['GET'])
def lti(tool):
    """
    Serve XML configuration for LTI integration
    """
    outxml = util.lticonfig(tool)
    if not outxml:
        abort(404)
    return Response(outxml, mimetype='text/xml')
