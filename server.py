
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
import random
import string
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from datetime import datetime
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.75.150.200/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.150.200/proj1part2"
#
DATABASEURI = "postgresql://xz2987:2485@34.75.150.200/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM students")
  users = []
  for result in cursor:
    users.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #s
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data=users)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#


@app.route('/allposts', methods=['POST', 'GET'])
def allposts():
  cursor = g.conn.execute("SELECT pid, content FROM posts")
  posts = []
  for result in cursor:
    posts.append((result['pid'], result['content']))  
  cursor.close()

  context = dict(data = posts)
  return render_template("allposts.html", **context)

@app.route('/events',methods=['POST','GET'])
def events():
  cursor = g.conn.execute("SELECT eid, type, description FROM events")
  events = []
  for result in cursor:
    events.append((result['eid'], result['type'],result['description']))  
  cursor.close()

  context = dict(data = events)
  return render_template("events.html", **context)

# Example of adding new data to the database

@app.route('/add_post', methods=['POST','GET'])
def add_post():
  sid = request.form['sid']
  content = request.form['content']
  pid = ''.join(random.sample(string.ascii_letters + string.digits, 10))
  date=datetime.today()
  time=datetime.now().time()
  try:
    if (g.conn.execute('select exists(select sid from students where sid=%s)',(sid))):
      g.conn.execute('INSERT INTO posts(pid, content, sid, post_date, post_time ) VALUES (%s, %s, %s, %s, %s)', [pid, content, sid, date, time])
      return redirect('/allposts')
  except:
    return render_template('login.html')

@app.route('/add_event', methods=['POST','GET'])
def add_event():
  sid = request.form['sid']
  eid = ''.join(random.sample(string.ascii_letters + string.digits, 10))
  type_of_event = request.form['type']
  #start_date=request.form['start_date']
  #start_time=request.form['start_time']
  #end_date=request.form['end_date']
  #end_time=request.form['end_time']
  s_number = request.form['s_number']
  street=request.form['street']
  city=request.form['city']
  state=request.form['state']
  zip=request.form['zip']
  description = request.form['description']

  #eid,type,start_date,start_time,end_date,end_time,s_number,street,city,state,zip,description 所有的column

  try:
    if (g.conn.execute('select exists(select sid from students where sid=%s)',(sid))):
      g.conn.execute('INSERT INTO events(eid,type,s_number,street,city,state,zip,description) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', 
      [eid,type_of_event,s_number,street,city,state,zip,description])
      return redirect('/events')
  except:
    return render_template('login.html')


@app.route('/login')
def login():
  return render_template("login.html")



@app.route('/add_login',methods=['POST','GET'])
def add_login():
  sid = request.form['sid']
  name = request.form['name']
  login = request.form['login']
  department = request.form['department']
  school = request.form['school']
  try:
    g.conn.execute('insert into students(sid, name, department, school, login) values (%s,%s,%s,%s,%s)',[sid,name,department,school,login])
    #if g.conn.execute('select exists(select sid from students where sid=%s)',[sid]):
    return render_template('index.html')
  except: 
    return 'You are already a user'


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
