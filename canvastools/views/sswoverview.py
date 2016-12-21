"""
Automatically redirect to the appropriate Social Work Course Overview website
"""
from flask import Blueprint
from flask import request, render_template, redirect
from ..common import util

TOOLNAME = 'sswoverview'

SSWOVERVIEW = Blueprint(TOOLNAME, __name__)
SSWBASE = 'https://www1.wjchen.org/sec/cu/ssw/ncwshares/courseoverview/'
COURSEID = 'lis_course_offering_sourcedid'

@SSWOVERVIEW.route('/launch', methods=['GET', 'POST'])
def frame():
    """
    Return the appropriate redirect for the SSW Course Overview website
    """
    param = {
        'debug': False,
        'https': True
        }

    if COURSEID in request.values:
        param['url'] = SSWBASE + request.values[COURSEID][:9] + '.html'
    else:
        param['error'] = "There was no course ID specified."

    if param['https'] and not param['debug']:
        return redirect(param['url'], code=302)
    else:
        return render_template('redirect.html', param=param)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')
