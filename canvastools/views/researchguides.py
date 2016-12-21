"""
Test Flask module for research guides

"""
from flask import Blueprint
from flask import request, render_template, redirect
from ..common import util

RESEARCHGUIDES = Blueprint('researchguides', __name__)

WEBROOT = '/var/www/html/tlaservice-web'

SAKAIDBNAME = util.CONFIG['app']['sakaidb']
DBCONFIG = util.CONFIG[SAKAIDBNAME]

RGURLHTTPS = 'https://www1.wjchen.org/sec-cgi-bin/cul/rschloc/rschloc?key='
RGURLHTTP = 'http://www.wjchen.org/cgi-bin/cul/rschloc?key='

def rgurl(cid):
    """
    Retrieve school and department from the database and generate a
    URL for the library redirect script

    """
    conn = util.dbconnect(DBCONFIG)
    curr = conn.cursor()

    param = {'https': False}
    queryparameters = {
        'site_id': cid
    }
    query = "SELECT SIS_DEPARTMENT, SIS_SCHOOL \
FROM CU_COURSE_SITE \
WHERE SITE_ID = :site_id"
    results = curr.execute(query, queryparameters).fetchall()
    if curr.rowcount > 0:
        param['url'] = RGURLHTTP + cid + '&dept=' + results[0][0] \
            + '&sch=' + results[0][1]
    else:
        param['url'] = RGURLHTTP + cid

    curr.close()
    conn.close()
    return param

@RESEARCHGUIDES.route('/launch', methods=['GET', 'POST'])
def frame():
    """
    This extracts the course ID from the LTI parameters and passes it
    to rgurl() to get the URL for the library redirect script.  The
    research guides do not have a Columbia HTTPS URL, so the tool
    generates a small HTML page that opens the research guide in a new
    window.
    """
    param = {
        'debug': False,
        'https': False
        }

    if 'lis_course_offering_sourcedid' in request.form:
        param.update(rgurl(request.form['lis_course_offering_sourcedid']))
    else:
        param['error'] = "There was no course ID specified."

    if param['https'] and not param['debug']:
        return redirect(param['url'], code=302)
    else:
        return render_template('redirect.html', param=param)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')
