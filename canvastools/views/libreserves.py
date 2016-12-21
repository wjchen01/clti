"""
Generate URL and redirect user to appropriate library reserves page
"""
import datetime

from flask import Blueprint
from flask import request, redirect, render_template
from ..common import util

LIBRESERVES = Blueprint('libreserves', __name__)

SAKAIDBNAME = util.CONFIG['app']['sakaidb']
DBCONFIG = util.CONFIG[SAKAIDBNAME]

def lrparam(cid, roles):
    """
    Given the course ID, this checks the database to see whether (a)
    reserves exist for the course and (b) the course is active
    (current or future semester).

    If the course is active and reserves exist, it returns the
    HTTPS URL of the reserves.  If the course is active and there are
    no reserves, and the user is an instructor it returns an HTTP URL
    inviting the user to set up reserves.  If the user is not an
    instructor it returns a message that reserves have not yet been set up.

    If the course is inactive and reserves exist, it returns the HTTPS
    URL of the reserves archive page (hosted on the Sakai server).  If
    the course is inactive and there were no reserves, it returns a
    message to that effect.
    """
    reservers = [
        'urn:lti:instrole:ims/lis/Administrator',
        'urn:lti:instrole:ims/lis/Instructor',
        'urn:lti:role:ims/lis/Instructor',
        'urn:lti:role:ims/lis/ContentDeveloper'
        ]

    param = {
        'info': 'Reserves for the course ' + cid + ' have not been set up.'
        }
    conn = util.dbconnect(DBCONFIG)
    curr = conn.cursor()
    queryparameters = {
        'site_id': cid
    }

    query = """SELECT registration
FROM SAKAI_SITE_TOOL
WHERE site_id = :site_id
AND substr(registration, 0, 21) = 'courseworks.reserves.'
"""

    results = curr.execute(query, queryparameters).fetchall()
    cidparts = cid.split('_')
    if curr.rowcount > 0:
        status = results[0][0][21:]
        if status == 'active':
            query = "SELECT SIS_REGISTRAR_SECTIONKEY \
FROM CU_COURSE_SITE \
WHERE SITE_ID = :site_id"
            results = curr.execute(query, queryparameters).fetchone()
            param['url'] = 'https://www1.wjchen.org/sec-cgi-bin/cul/\
respac/respac?CRSE=' + results[0]
            param['info'] = ""
        elif status == 'static' and len(cidparts) > 3:
            param['url'] = 'https://courseworks.wjchen.org/reserves/'\
                + cidparts[2] + '_' + cidparts[3] + '/' + cid\
                + '-reserves.shtml'
            param['info'] = ""
    if 'url' not in param:
        # is this course active?
        if len(cidparts) > 3:
            try:
                _ = int(cidparts[2])
                _ = int(cidparts[3])
            except ValueError:
                cidparts[2] = 0
                cidparts[3] = 0

            if int(cidparts[2]) >= datetime.date.today().year and \
                    int(cidparts[3]) >= util.current_semester(curr):
                # is the user an instructor?
                setuprole = False
                param['info'] = 'Reserves for the course '\
                    + cid + ' have not been set up.'
                for i in roles.split(','):
                    if i in reservers:
                        setuprole = True
                if setuprole:
                    param['url'] = 'http://library.wjchen.org/find/\
reserves.html'
                    param['info'] = ""
            else:
                param['info'] = "There were no reserves for the course "\
                    + cid + '.'
        else:
            param['info'] = "There were no reserves for the course "\
                + cid + '.'

    curr.close()
    conn.close()
    return param

@LIBRESERVES.route("/launch", methods=['GET', 'POST'])
def library_reserves():
    """
    This extracts the course ID and user role (student, teacher, etc.)
    from the LTI parameters and passes them to lrparam() to get the
    appropriate URL or message.  If there is a message, it generates a
    page with that message.  If there is an HTTP URL, it generates a
    page that opens the URL in a new window.  If there is an HTTPS
    URL, it redirects the browser to that URL.
    """
    cid = ''
    param = {
        'title': 'Library Reserves',
        'https': False,
        }
    if 'lis_course_offering_sourcedid' in request.values:
        cid = request.values['lis_course_offering_sourcedid']
    elif 'context_id' in request.values:
        cid = request.values['context_label']
    if len(cid) > 0:
        param.update(
            lrparam(
                cid,
                request.values['ext_roles']
                )
            )
    else:
        param['error'] = "There was no course ID specified."

    if 'url' in param and param['url'][0:5] == 'https':
        param['https'] = True
        return redirect(param['url'], code=302)
    else:
        return render_template('redirect.html', param=param)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')
