#!/usr/bin/env python3
import dotenv
import sys
import re
import json
import os
import logging
import yaml
import glob
import copy
import datetime
import jsonpath_ng
import urllib.parse
import importlib
from string import Template
from flask import Flask, request, render_template, make_response, g
from jinja2 import Environment, select_autoescape
from werkzeug.middleware.proxy_fix import ProxyFix

has_dotenv = True if os.environ.get('DOTENV') != None else False
dotenv.load_dotenv(os.environ.get('DOTENV','.env'), verbose = has_dotenv, override = has_dotenv)

verbose = int(os.environ.get('VERBOSE','1'))
port = int(os.environ.get('PORT','5000'))
#datadir = os.environ.get('DATADIR','data')

logging.basicConfig(level=logging.WARNING-10*verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")

Flask.jinja_options = {
    'autoescape': select_autoescape(
        disabled_extensions=('txt'),
        default_for_string=True,
        default=True),
    'line_statement_prefix': '%'
}
app = Flask(__name__)


@app.route("/",methods = ['GET', 'POST'])
def index():
    results = [[1,"a"],[2,"b"]]
    streamnames = ['aaa','bbb']
    errormsg = None

    if request.method == 'POST':
        args = request.form
    else:
        args = request.args

    try:
        query = args.get('query')
    except Exception as e:
        errormsg = repr(e)
        logging.exception("Error while generating results:")

    logging.debug(f"Results: {yaml.dump(results)}")

    if args.get('output') == "yaml" and not errormsg:
        response = make_response(yaml.dump(results), 200)
        response.mimetype = "text/plain"
        return response

    return render_template('index.html.jinja', args=args, streamnames=streamnames, results=results, errormsg=errormsg )


@app.before_request
def start_timer():
  g.time_start = datetime.datetime.now()

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers["Cache-Control"] = "no-store, max-age=0"

    if 'time_start' in g:
        page_duration = datetime.datetime.now() - g.time_start
        page_duration_fmt = f"{page_duration.total_seconds():.3f}"
        if response.response and 200 <= response.status_code < 300 and response.content_type.startswith('text/html'):
            response.set_data(response.get_data().replace(b'%PAGETIME%', bytes(page_duration_fmt, 'utf-8')))

    return response

app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
