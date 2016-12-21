"""
Common filters for Columbia University LTI tools
"""
import datetime
from time import strftime
import flask
from ..common import util

FILTERS = flask.Blueprint('filters', __name__)

@FILTERS.app_template_filter('datenice')
def dateniceformat(ts, fmt):
    """
    Format date according to **fmt**
    """
    dt = datetime.datetime.fromtimestamp(ts / 1e3)
    return dt.strftime(fmt)
#

@FILTERS.app_template_filter('deltanice')
def deltanice(ms):
    """
    Format a time difference in minutes and seconds
    """
    seconds = round(ms / 1e3)
    td = datetime.timedelta(seconds=seconds)
    tdparts = str(td).split(':')
    return td
#    return ':'.join(tdparts[:2]) + ':' + str(round(float(tdparts[2])))

@FILTERS.app_template_filter('role')
def role(enrollment):
    """
    Return short name for role
    """
    shortrole = enrollment
    if enrollment in util.ENROLLMENTS:
        shortrole = util.ENROLLMENTS[enrollment]
    return shortrole

@FILTERS.app_template_filter('jenkins2strap')
def j2strap(status):
    """
    Translate Jenkins status into Bootstrap styles
    """
    bstatus = status;
    if status in util.JENKINSSTATUS:
        bstatus = util.JENKINSSTATUS[status]['strap']
    return bstatus

@FILTERS.app_template_filter('jenkins2color')
def j2color(status):
    """
    Translate Jenkins status into icon colors
    """
    istatus = status;
    if status in util.JENKINSSTATUS:
        istatus = util.JENKINSSTATUS[status]['color']
    return istatus
