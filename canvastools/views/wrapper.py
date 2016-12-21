"""
Flask APP to wrap Sakai pages in LTI tools for the Columbia University
Courseworks program

"""

import logging
import json
import cx_Oracle
from os import path
from flask import Blueprint, request, redirect, abort
from ..common import util

wrapper = Blueprint('wrapper', __name__)

SAKAIDBNAME = util.CONFIG['app']['sakaidb']
DBCONFIG = util.CONFIG[SAKAIDBNAME]

def sakai_tool(sakaitool):
    """
    sakai_tool enables us to connect to sakai db to find the site-id of any coursename provided
    """
    conn = util.dbconnect(DBCONFIG)
    curr = conn.cursor()
    queryparameters = {
        'sakai_tool': sakaitool,
        'site_id': str(request.form['lis_course_offering_sourcedid'])
    }
    if request.form['lti_message_type'] == 'basic-lti-launch-request'\
            and request.form['lti_version'] == "LTI-1p0":
        query = "SELECT tool_id FROM SAKAI_SITE_TOOL " +\
            "WHERE site_id=:site_id AND registration=:sakai_tool"
        toolid = curr.execute(query, queryparameters).fetchall()
        if curr.rowcount == 0:
            return "<h1>There is no tool available on sakai matching: {}</h1>"\
                .format(queryparameters['sakai_tool'])
        else:
            url = util.CONFIG['app']['sakai_url'] + "/portal/tool/{}"\
                .format(str(toolid[0][0]))
            return redirect(url, code=302)
    else:
        abort(401)

    curr.close()
    conn.close()


@wrapper.route("/info/launch", methods=['GET', 'POST'])
def info_tool():
    """
    Course information imported from sakai
    """
    return sakai_tool('sakai.iframe.site')


@wrapper.route("/mail/launch", methods=['GET', 'POST'])
def mail_tool():
    """
    Mail Tool imported from sakai
    """
    return sakai_tool('sakai.mailtool')


@wrapper.route("/signup/launch", methods=['GET', 'POST'])
def sign_up():
    """
    Sign Up Tool imported from sakai
    """
    return sakai_tool('sakai.signup')

@wrapper.route("/evaluation/launch", methods=['GET','POST'])
def evaluation():
    """
    Evaluation from sakai
    """
    return sakai_tool('sakai.rsf.evaluation')

@wrapper.route("/dropbox/launch", methods=['GET','POST'])
def dropbox():
    """
    Wrapper tool for Sakai dropbox
    """
    return sakai_tool('sakai.dropbox')

@wrapper.route("/roster/launch", methods=['GET', 'POST'])
def photo_roster():
    return sakai_tool('sakai.site.roster')


@wrapper.route("/wikispaces/launch", methods=['GET', 'POST'])
def wikispaces():
    """
    Wrapper tool for Wikispaces
    """
    if request.form['lti_message_type'] == 'basic-lti-launch-request' and request.form['lti_version'] == "LTI-1p0":
        year = request.form['lis_course_offering_sourcedid'][14:18]
        term = request.form['lis_course_offering_sourcedid'][19:20]
        dept_code = request.form['lis_course_offering_sourcedid'][0:4]
        course_number = request.form['lis_course_offering_sourcedid'][5:9]
        prefix = request.form['lis_course_offering_sourcedid'][4:5]
        section = request.form['lis_course_offering_sourcedid'][10:13]
        url = "https://www1.wjchen.org/sec-cgi-bin/ccnmtl/projects/wikispaces-admin/courseworks_wikispaces.php?CRSE={}{}{}{}{}{}".format(year,term, dept_code, course_number, prefix, section)
        return redirect(url, code=302)
    else:
        abort(401)

