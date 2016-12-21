"""
Template for Canvas LTI tool
"""
from flask import Blueprint, Flask, Response
from flask import render_template
from ..common import util

template = Blueprint('template', __name__)

@template.route('/launch', methods=['GET', 'POST'])
def tool():
    """
    This is run on the initial launch of the tool
    """
    param = {
        'debug': False,
        'info': 'This is a test'
        }

    return render_template('redirect.html', param=param)

if __name__ == "__main__":
    print('This requires Flask and Blueprint')

