import sys
import os
##Virtualenv Settings

activate_this = '/var/www/html/tlaservice-web/venv/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

if sys.version_info[0]<3:       # require python3
    raise Exception("Python3 required! Current (wrong) version: '%s'" % sys.version_info)

sys.path.insert(0, '/var/www/html/tlaservice-web')

from canvastools import app as application
application.secret_key = '\xca\x8c@YGH8\x90\x83\x08$+\xe9\xab\xc8\xcckG\xe9\xadi\x8ev\x81'

# os.environ['DEBUG'] = "1"
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
