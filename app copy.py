import sqlite3
import csv
import sys
import os
import json
import re
from flask import Flask, redirect, url_for, Response,  make_response, request, current_app
from werkzeug import secure_filename
from datetime import timedelta
from functools import update_wrapper
from flask import render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/index')
def hello(name=None):
    return render_template('gabe.html')

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route("/api/<country>/<state>/<year>/<cla>")
def patent(country, state, year, cla):
      print state
      import json
      #conn = sqlite3.connect('/data/patentdata/LATEST/invpat.sqlite3')
      conn = sqlite3.connect('/Users/kevshin2/Documents/Fung_mapper/Patent_mapper/invpat.sqlite3')
      c = conn.cursor()
      if state == "empty" and cla == "empty":
          print "not here"
          c.execute('''
            select Patent, Longitude, Latitude, Lastname, Firstname, Assignee, AppYear, Gyear, State, City, Country from invpat where Country = "{country}" AND AppYear = {year} limit 35000;
          '''.format(year=year,country=country))
          
      elif state == "empty" and cla != "empty":
          print "here"
          c.execute('''
            select Patent, Longitude, Latitude, Lastname, Firstname, Assignee, AppYear, Gyear, State, City, Country from invpat where Country = "{country}" AND AppYear = {year} AND Class like "{cla}/%" limit 35000;
          '''.format(year=year, cla=cla, country=country))
      elif cla != "empty":
          print "here2"
          c.execute('''
            select Patent, Longitude, Latitude, Lastname, Firstname, Assignee, AppYear, Gyear, State, City, Country from invpat where State = "{state}" AND AppYear = {year} And Class like "{cla}/%" limit 30000;
          '''.format(state=state, year=year, cla=cla))
         #;
         #select Patent, Latitude, Longitude, count(*) from (select * from invpat where State = "{state}" and AppYear = {year} And Class like "{cla}/%") group by Latitude, Longitude limit 200;
      else :
          print "here3"
          c.execute('''
            select Patent, Longitude, Latitude, Lastname, Firstname, Assignee, AppYear, Gyear, State, City, Country from (select * from (select * from invpat where State = "{state}") where AppYear = {year});
                  '''.format(state=state, year=year))
      #
      #select Patent, Longitude, Latitude from (select * from invpat where State = "{state}" and AppYear = {year}) group by Latitude, Longitude;
      results = c.fetchall()
      d = dict(zip([x[0] for x in results],[x[1:] for x in results]))
      jsonout = json.dumps(d, indent=4)
      if 'callback' in request.args:
        jsonout = "{callback}({json})".format(callback=request.args["callback"], json=jsonout)
      elif 'jsonp' in request.args:
        jsonout = "{callback}({json})".format(callback=request.args["jsonp"], json=jsonout)
      return Response(jsonout, mimetype="application/json")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in 'tsv, csv'

@app.route("/upload/", methods=['POST'])
def upload_file():
    print request
    print 'im here'
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #print filepath
        file.save(filepath)
        print 'im inside'
        return parse(filepath)

def parse(filename):
  f = open(filename, 'rb')
  #conn = sqlite3.connect('/data/patentdata/LATEST/invpat.sqlite3')
  conn = sqlite3.connect('/Users/kevshin2/Documents/Fung_mapper/Patent_mapper/invpat.sqlite3')
  c = conn.cursor()
  results = []
  print 'ready'
  for line in f:
    print line
    line = int(line.strip())
    c.execute('''
      select Patent, Longitude, Latitude, Lastname, Firstname, Assignee, AppYear, Gyear, State, City from invpat where Patent = "0{pat}";
      '''.format(pat=line))
    results += c.fetchall()
  d = dict(zip([x[0] for x in results],[x[1:] for x in results]))
  jsonout = json.dumps(d, indent=4)
  if 'callback' in request.args:
    jsonout = "{callback}({json})".format(callback=request.args["callback"], json=jsonout)
  elif 'jsonp' in request.args:
    jsonout = "{callback}({json})".format(callback=request.args["jsonp"], json=jsonout)
  return Response(jsonout, mimetype="application/json")


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
