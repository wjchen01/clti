"""
Retrieve feed and build information from Jenkins, and display list of LTI tools
"""
import json
import logging
from datetime import datetime
from pretty_cron import prettify_cron
import defusedxml.ElementTree as ET
from flask import Blueprint, Flask, current_app, Response, redirect
from flask import render_template, abort, session, jsonify, request
from xml.sax.saxutils import quoteattr
from jenkins import Jenkins, NotFoundException
from ..common import util, auth

TOOLNAME = 'dash'
DASH = Blueprint(TOOLNAME, __name__)

TCONFIG = util.CONFIG[TOOLNAME]
LOG = logging.getLogger(__name__)

JURL = 'https://jenkins.cc.wjchen.org/'

JENKINSAPI = Jenkins(
    JURL,
    username=TCONFIG['devid'],
    password=TCONFIG['devkey']
    )

CASURL = util.CONFIG['app']['CAS_SERVER'] + '/cas/login?TARGET='\
    + util.CONFIG['app']['SERVER_NAME'] + '/' + TOOLNAME + '/'

CAS2URL = util.CONFIG['app']['CAS_SERVER'] + '/cas/login?service='\
    + util.CONFIG['app']['SERVER_NAME'] + '/' + TOOLNAME + '/'

@DASH.route('/console/<job>/<build>', methods=['GET'])
def console(job, build):
    """
    Retrieve console output from Jenkins
    """
    if 'casok' not in session:
        abort(401)
    if not job or not build:
        abort(400)
    try:
        _ = int(build)
    except:
        abort(400)
    try:
        output = JENKINSAPI.get_build_console_output(job, int(build))
    except NotFoundException:
        abort(404)
    return output

@DASH.route('/job/<job>', methods=['GET'])
def sjob(job=None):
    """
    Display the job requested by the user.

    Possibly filter by job
    """
    jobinfo = {}
    ajax = False

    if 'casok' not in session:
        abort(401)
    if not job:
        LOG.error("No job specified!")
        abort(404)

    if job not in TCONFIG['feeds'] + TCONFIG['builds']:
        LOG.error("Not our job: " + job)
        abort(401)

    if 'builds' in request.values:
        try:
            builds = int(request.values['builds'])
        except:
            LOG.error(
                "Build number not an integer: " + request.values['builds']
                )

    param = {
        'debug': False,
        'jurl': JURL,
        'imageurl': 'static/8197d45d/images/',
        'builds': None,
        'sched': '',
        'ajax': ajax
        }
    try:
        param['results'] = JENKINSAPI.get_job_info(
            job,
            depth=1
            )
    except NotFoundException:
        LOG.error("Not found: " + job)
        abort(404)

    lastBuild = datetime.fromtimestamp(
        param['results']['lastBuild']['timestamp'] / 1e3
        )
    
    croot = ET.fromstring(JENKINSAPI.get_job_config(job))
    ctrig = None
    cspec = None
    ctrigs = croot.find('triggers')
    if ctrigs:
        ctrig = ctrigs.find('hudson.triggers.TimerTrigger')
        if ctrig:
            cspec = ctrig.find('spec')
            if cspec.text:
                param['sched'] = prettify_cron(cspec.text)

    if 'ajax' in request.values:
        quo = { '"': '&quot;' }
        param['ajax'] = request.values['ajax']
        if request.values['ajax']:
            param['builds'] = 5
        jobhtml = quoteattr(
            render_template('feedjob.html', param=param),
            quo
            )
        iconshtml = quoteattr(
            render_template('jobicons.html', param=param),
            quo
            )
        outjson = '{"list": ' + jobhtml + ', "icons": ' + iconshtml\
            + ', "sched": ' + json.dumps(param['sched'])\
            + ', "lastBuild": "' + lastBuild.ctime() + '" }'
        return outjson
    else:
        return render_template('feedjob.html', param=param)

@DASH.route('/', methods=['GET', 'POST'])
def dashtool():
    """
    Display basic dashboard
    """
    if 'casok' not in session:
        if 'SAMLart' not in request.values:
            return redirect(CASURL)
        else:
            casok = auth.cas(request.values['SAMLart'], TOOLNAME, 'CUNIX_tlt')
            if not casok:
                abort(401)
            session['casok'] = casok
    print("dash CAS OK: " + str(session['casok']))

    if 'tlacasapp' in session:
        if session['tlacasapp'] == 'tools':
            session['tlacasapp'] = None
            return redirect('/dash/tools')
    # TODO get builds as well as feeds
    session['tlacasapp'] = None
    param = {
        'debug': False,
        'jurl': JURL,
        'imageurl': 'static/71735edb/images/',
        'jobs': [],
        'configs': []
        }
    for job in JENKINSAPI.get_jobs():
        if job['name'] in TCONFIG['feeds']:
            try:
                param['jobs'].append(
                    JENKINSAPI.get_job_info(
                        job['name']
                        )
                    )
            except NotFoundException as e:
                LOG.error("No info found for job " + job['name'])
    return render_template('feeds.html', param=param)

@DASH.route('/tools', methods=['GET', 'POST'])
def tools():
    """
    Display list of LTI tools with URLs for XML and keys
    """
    if 'casok' not in session:
        if 'ticket' not in request.values:
            session['tlacasapp'] = 'tools'
            return redirect(CASURL)
        else:
            casok = auth.cas(request.values['ticket'], TOOLNAME, 'CUNIX_tlt')
            if not casok:
                abort(401)
            session['casok'] = casok

    param = {
        'debug': False,
        'server_url': util.CONFIG['app']['SERVER_NAME'],
        'config': {}
        }

    for tool in util.CONFIG['app']['apps']:
        param['config'][tool] = util.CONFIG[tool]

    return render_template('tools.html', param=param)

@DASH.route('/subaccount-move', methods=['GET', 'POST'])
def subaccount_move():
    """
    Move courses fromone subdomain to another
    """
    if 'uni' not in session:
        if 'ticket' not in request.values:
            session['tlacasapp'] = 'subaccount-move'
            return redirect(CAS2URL)
        else:
            casok = auth.cas(request.values['ticket'], TOOLNAME)
            print(casok)
            if not casok:
                abort(401)
            session['uni'] = casok
    else:
        print("session['uni'] = " + session['uni'])
    param = {
        'uni': session['uni']
        }
    session['tlacasapp'] = None
    return render_template('samove.html', param=param)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')

