'''
canvastools/__init__.py
'''

from flask import Flask, render_template
app = Flask(__name__)
app.config.from_json('config.json')

from .common import util
from pathlib import Path
from .common.filters import FILTERS
from .views.misc import MISC
from .views.libreserves import LIBRESERVES
from .views.researchguides import RESEARCHGUIDES
from .views.roster import ROSTER
from .views.dash import DASH
# from .views.admin import ADMIN
from .views.submitgd import SUBMITGD
# from .views.courseinfo import COURSEINFO
from .views.sswoverview import SSWOVERVIEW
from .views.wrapper import wrapper

app.register_blueprint(LIBRESERVES, url_prefix='/libreserves')
app.register_blueprint(LIBRESERVES, url_prefix='/libraryreserves')
app.register_blueprint(RESEARCHGUIDES, url_prefix='/researchguides')
# app.register_blueprint(ROSTER, url_prefix='/roster')
app.register_blueprint(SUBMITGD, url_prefix='/submit')
app.register_blueprint(DASH, url_prefix='/dash')
# app.register_blueprint(ADMIN, url_prefix='/admin')
# app.register_blueprint(COURSEINFO, url_prefix='/courseinfo')
app.register_blueprint(SSWOVERVIEW, url_prefix='/sswoverview')
app.register_blueprint(MISC)
app.register_blueprint(FILTERS)
app.register_blueprint(wrapper)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
