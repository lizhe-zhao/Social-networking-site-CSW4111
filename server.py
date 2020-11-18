
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
from flask import Flask, request, render_template, g, redirect, Response, url_for

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
  cursor = g.conn.execute("with cte as(select p.pid, sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid, p.content,s.name,p.post_date,p.post_time,coalesce(c.net_count,0) from posts p left join students s on s.sid=p.sid left join cte c on c.pid=p.pid")
  posts = []
  for result in cursor:
    posts.append((result[0], result[1],result[2],result[3],result[4],result[5]))  
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
  start_date=request.form['start_date']
  start_time=request.form['start_time']
  end_date=request.form['end_date']
  end_time=request.form['end_time']
  s_number = request.form['s_number']
  street=request.form['street']
  city=request.form['city']
  state=request.form['state']
  zip=request.form['zip']
  description = request.form['description']
  capacity=request.form['capacity']

  cursor=g.conn.execute('select exists(select sid from students where sid=%s)',(sid))
  A=cursor.fetchone()[0]
  cursor.close()
  if A:
    g.conn.execute('INSERT INTO events(eid,type,start_date,start_time,end_date,end_time,s_number,street,city,state,zip,description,capacity) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', [eid,type_of_event,start_date,start_time,end_date,end_time,s_number,street,city,state,zip,description,capacity])
    g.conn.execute('insert into host(sid,eid,type) values (%s,%s,%s)',[sid,eid,'per'])
    return redirect('/events')
  else:
    return render_template('login.html')

@app.route('/co_host/<eid>',methods=['POST','GET'])
def co_host(eid=None):
  sid=request.form['sid']
  eid=eid
  cursor=g.conn.execute('select exists(select sid from students where sid=%s)',(sid))
  A=cursor.fetchone()[0]
  cursor.close()
  if A:
    g.conn.execute('insert into host(sid,eid) values (%s,%s)', [sid,eid])
    g.conn.execute("update host SET type='org' WHERE eid=%s",(eid))
    return redirect(url_for('eventdetail',eid=eid))
  else:
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
    return redirect('/')
  except: 
    txt='You are already a user'
    return render_template('test.html',message=txt)


@app.route('/id',methods=['GET','POST'])
def id():
  if request.method=='POST':
    sid=request.form['sid']
    login=request.form['login']
    cursor=g.conn.execute('select login from students where sid=%s',(sid))
    email=cursor.fetchone()[0]
    cursor.close()
    if login==email:
      return redirect(url_for('profile',sid=sid))
    else:
      err='sid and email incorrect'
      return render_template('id.html',data=err)
  return render_template('id.html')

@app.route('/profile/<sid>',methods=['GET','POST'])
def profile(sid=None):
  #sid = request.args.get('sid',None)
  sid=sid
  cursor = g.conn.execute("SELECT pid, content FROM posts where sid=%s",(sid))
  posts = []
  for result in cursor:
    posts.append((result['pid'], result['content']))  
  cursor.close()
  
  cursor = g.conn.execute("select e.eid,e.type,e.description from (SELECT eid FROM attend where sid=%s) as A, events e where A.eid=e.eid",(sid))
  events = []
  for result in cursor:
    events.append((result['eid'], result['type'],result['description']))  
  cursor.close()

  cursor = g.conn.execute("select e.eid, e.type, e.description from events e, currently_at at where e.city=at.city and at.sid=%s",(sid))
  eventsatloc = []
  for result in cursor:
    eventsatloc.append((result['eid'], result['type'],result['description']))  
  cursor.close()

  cursor=g.conn.execute('select sid, city from currently_at where sid=%s',(sid))
  loc=cursor.fetchone()
  cursor.close()

  cursor = g.conn.execute("select e.eid,e.type,e.description from (SELECT eid FROM host where sid=%s) as A, events e where A.eid=e.eid",(sid))
  host = []
  for result in cursor:
    host.append((result['eid'], result['type'],result['description']))  
  cursor.close()

  context = dict(data1 = posts,data2=events,data3=eventsatloc,data4=loc,data5=host)
  return render_template("profile.html",**context)


@app.route('/postdetail/<pid>',methods=['GET','POST'])
def postdetail(pid=None):
  cursor = g.conn.execute("SELECT p.pid, p.content, s.name, p.post_date, p.post_time FROM students s, posts p where p.pid=%s and s.sid=p.sid",(pid))
  post=cursor.fetchone()
  cursor.close()

  cursor = g.conn.execute("with cte as(select p.pid,sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid,coalesce(c.net_count,0) as net,coalesce(c.total,0) as total from posts p left join cte c on p.pid=c.pid where p.pid=%s",(pid))
  vote=cursor.fetchone()
  cursor.close()

  cursor = g.conn.execute("select s.name, c.content from comments_of_posts c, students s, posts_have ph where ph.pcid=c.pcid and s.sid=c.sid and ph.pid=%s",(pid))
  comments=[]
  for c in cursor:
    comments.append((c[0],c[1]))
  cursor.close()

  context=dict(data1=post,data2=vote,data3=comments)
  return render_template('postdetail.html',**context)

@app.route('/add_comment/<pid>', methods=['POST','GET'])
def add_comment(pid=None):
  sid = request.form['sid']
  content = request.form['comment']
  pcid = ''.join(random.sample(string.ascii_letters + string.digits, 10))
  comment_date = datetime.today()
  comment_time = datetime.now().time() 
  cursor = g.conn.execute('INSERT INTO comments_of_posts(pcid, sid, content, comment_date, comment_time ) VALUES (%s, %s, %s, %s, %s)', [pcid, sid, content, comment_date, comment_time])
  cursor.close()
  cursor = g.conn.execute('INSERT INTO posts_have(pcid, pid) VALUES (%s, %s)', [pcid, pid])
  cursor.close()
  return redirect(url_for('postdetail',pid=pid))

@app.route('/eventdetail/<eid>',methods=['GET','POST'])
def eventdetail(eid=None):
  cursor = g.conn.execute("SELECT e.eid, e.description, s.name, e.start_date, e.start_time, e.end_date, e.end_time, e.capacity, h.type FROM students s, events e, host h where e.eid=%s and h.eid=e.eid and h.sid=s.sid",(eid))
  id=set(); description=set(); hosts=set()
  start_date=set();start_time=set();end_date=set();end_time=set();capacity=set();type=set()
  for res in cursor:
    id.add(res[0])
    description.add(res[1])
    hosts.add(res[2])
    start_date.add(res[3])
    start_time.add(res[4])
    end_date.add(res[5])
    end_time.add(res[6])
    capacity.add(res[7])
    type.add(res[8])
  cursor.close()

  cursor=g.conn.execute("select s_number,street,city,state,zip from events where eid=%s",(eid))
  location=[]
  for l in cursor:
    location.append((l[0],l[1],l[2],l[3],l[4]))
  cursor.close

  cursor = g.conn.execute("select s.name, c.content from comments_of_events c, students s, event_have eh where eh.ecid=c.ecid and s.sid=c.sid and eh.eid=%s",(eid))
  comments=[]
  for c in cursor:
    comments.append((c[0],c[1]))
  cursor.close()

  cursor = g.conn.execute("with cte as(select e.eid, sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from events e, event_vote v where e.eid=v.eid group by e.eid) select e.eid,coalesce(c.net_count,0),coalesce(c.total,0) from events e left join cte c on c.eid=e.eid where e.eid=%s",(eid))
  vote=cursor.fetchone()
  cursor.close()
  
  cursor=g.conn.execute('select e.eid, coalesce(e.capacity,100), coalesce(count(a.sid),0) from events e left join attend a on e.eid=a.eid where a.eid=%s group by e.eid',(eid))
  capacity=cursor.fetchone()
  cursor.close()

  context=dict(data1=id,data2=description,data3=hosts,data4=start_date,data5=start_time,data6=end_date,data7=end_time,data8=capacity,data9=type,loc=location,com=comments,vote=vote,capacity=capacity)
  return render_template('eventdetail.html',**context)

@app.route('/add_event_comment/<eid>', methods=['POST','GET'])
def add_event_comment(eid=None):
  sid = request.form['sid']
  content = request.form['comment']
  ecid = ''.join(random.sample(string.ascii_letters + string.digits, 10))
  comment_date = datetime.today()
  comment_time = datetime.now().time() 
  cursor = g.conn.execute('INSERT INTO comments_of_events(ecid, sid, content, comment_date, comment_time ) VALUES (%s, %s, %s, %s, %s)', [ecid, sid, content, comment_date, comment_time])
  cursor.close()
  cursor = g.conn.execute('INSERT INTO event_have(ecid, eid) VALUES (%s, %s)', [ecid, eid])
  cursor.close()
  return redirect(url_for('eventdetail',eid=eid))

@app.route('/sort_posts',methods=['POST','GET'])
def sort_posts():
  cond=request.form['cond']
  posts=[]
  if cond=='timeL':
    cursor=g.conn.execute("with cte as(select p.pid,sum(case when v.type='up' then 1 else -1 end)as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid, p.content,s.name,p.post_date,p.post_time,coalesce(c.net_count,0) from posts p left join students s on s.sid=p.sid left join cte c on c.pid=p.pid order by p.post_date desc,p.post_time desc")
  elif cond=='timeO':
    cursor=g.conn.execute("with cte as(select p.pid,sum(case when v.type='up' then 1 else -1 end)as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid, p.content,s.name,p.post_date,p.post_time,coalesce(c.net_count,0) from posts p left join students s on s.sid=p.sid left join cte c on c.pid=p.pid order by p.post_date asc,p.post_time asc")
  elif cond=='popA':
    cursor = g.conn.execute("with cte as(select p.pid,sum(case when v.type='up' then 1 else -1 end)as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid, p.content,s.name,p.post_date,p.post_time,coalesce(c.net_count,0) from posts p left join students s on s.sid=p.sid left join cte c on c.pid=p.pid order by c.net_count asc")
  elif cond=='popD':
    cursor = g.conn.execute("with cte as(select p.pid,sum(case when v.type='up' then 1 else -1 end)as net_count, count(*) as total from posts p, post_vote v where p.pid=v.pid group by p.pid) select p.pid, p.content,s.name,p.post_date,p.post_time,coalesce(c.net_count,0) from posts p left join students s on s.sid=p.sid left join cte c on c.pid=p.pid order by c.net_count desc")
  
  for result in cursor:
    posts.append((result[0], result[1],result[2],result[3],result[4],result[5]))  
  cursor.close()
  
  context=dict(data=posts)
  return render_template('allposts.html',**context)


@app.route('/sort_events',methods=['POST','GET'])
def sort_events():
  cond=request.form['cond']
  posts=[]
  if cond=='timeL':
    cursor=g.conn.execute("with cte as(select e.eid,sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from events e, event_vote v where e.eid=v.eid group by e.eid) select e.eid, e.description, s.name, e.start_date, e.start_time, coalesce(c.net_count,0) from events e left join host h on e.eid=h.eid left join students s on h.sid=s.sid left join cte c on c.eid=e.eid order by e.start_date desc, e.start_time desc")
  elif cond=='timeO':
    cursor=g.conn.execute("with cte as(select e.eid,sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from events e, event_vote v where e.eid=v.eid group by e.eid) select e.eid, e.description, s.name, e.start_date, e.start_time, coalesce(c.net_count,0) from events e left join host h on e.eid=h.eid left join students s on h.sid=s.sid left join cte c on c.eid=e.eid order by e.start_date asc, e.start_time asc")
  elif cond=='popA':
    cursor = g.conn.execute("with cte as(select e.eid,sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from events e, event_vote v where e.eid=v.eid group by e.eid) select e.eid, e.description, s.name, e.start_date, e.start_time,coalesce(c.net_count,0) from events e left join host h on e.eid=h.eid left join students s on h.sid=s.sid left join cte c on c.eid=e.eid order by c.net_count asc")
  elif cond=='popD':
    cursor = g.conn.execute("with cte as(select e.eid,sum(case when v.type='up' then 1 else -1 end) as net_count, count(*) as total from events e, event_vote v where e.eid=v.eid group by e.eid) select e.eid, e.description, s.name, e.start_date, e.start_time, coalesce(c.net_count,0) from events e left join host h on e.eid=h.eid left join students s on h.sid=s.sid left join cte c on c.eid=e.eid order by c.net_count desc")
  
  for result in cursor:
    posts.append((result[0], result[1],result[2],result[3],result[4],result[5]))  
  cursor.close()
  
  context=dict(data=posts)
  return render_template('events.html',**context)


@app.route('/update_loc/<sid>',methods=['GET','POST'])
def update_loc(sid=None):
  s_number = request.form['s_number']
  street=request.form['street']
  city=request.form['city']
  state=request.form['state']
  zip=request.form['zip']
  if sid:
    try:
      g.conn.execute('insert into locations (s_number,street,city,state,zip) values (%s,%s,%s,%s,%s)',[s_number,street,city,state,zip])
    except:
      pass
    g.conn.execute("UPDATE currently_at SET s_number=%s,street=%s,city=%s,state=%s,zip=%s WHERE sid=%s",[s_number,street,city,state,zip,sid])
  return redirect(url_for('profile',sid=sid))

@app.route('/vote_post/<pid>',methods=['POST','GET'])
def vote_post(pid=None):
  cond = request.form['cond']
  sid = request.form['sid']
  pid=pid
  cursor=g.conn.execute('select exists(select sid from students where sid=%s)',(sid))
  A=cursor.fetchone()[0]
  cursor.close()
  if A:
    cursor=g.conn.execute('select exists(select sid,pid from post_vote where sid=%s and pid=%s)',[sid,pid])
    B=cursor.fetchone()[0]
    cursor.close()
    if not B:
      if cond=='Up':
        g.conn.execute('INSERT INTO post_vote(sid, pid, type) VALUES (%s, %s, %s)', [sid, pid, 'up'])
      elif cond=='Down':
        g.conn.execute('INSERT INTO post_vote(sid, pid, type) VALUES (%s, %s, %s)', [sid, pid, 'down'])
      return redirect(url_for('postdetail',pid=pid))
    else:
      txt='You have voted for this post.'
      return render_template('test.html',message=txt)
  else:
    return render_template('login.html')

@app.route('/vote_event/<eid>',methods=['POST','GET'])
def vote_event(eid=None):
  cond = request.form['cond']
  sid = request.form['sid']
  eid=eid
  cursor=g.conn.execute('select exists(select sid from students where sid=%s)',(sid))
  A=cursor.fetchone()[0]
  cursor.close()
  if A:
    cursor=g.conn.execute('select exists(select sid,eid from event_vote where sid=%s and eid=%s)',[sid,eid])
    B=cursor.fetchone()[0]
    cursor.close()
    if not B:
      if cond=='Up':
        g.conn.execute('INSERT INTO event_vote (sid, eid, type) VALUES (%s, %s, %s)', [sid, eid, 'up'])
      elif cond=='Down':
        g.conn.execute('INSERT INTO event_vote (sid, eid, type) VALUES (%s, %s, %s)', [sid, eid, 'down'])
      return redirect(url_for('eventdetail',eid=eid))
    else:
      txt='You have voted for this event.'
      return render_template('test.html',message=txt)
  else:
    return render_template('login.html')

@app.route('/joinevent/<eid>',methods=['POST','GET'])
def joinevent(eid=None):
  cond=request.form['cond']
  sid=request.form['sid']
  eid=eid
  cursor=g.conn.execute('select exists(select sid from students where sid=%s)',(sid))
  A=cursor.fetchone()[0]
  cursor.close()
  if A:
    cursor=g.conn.execute('select exists(select sid,eid from attend where sid=%s and eid=%s)',[sid,eid])
    B=cursor.fetchone()[0]
    cursor.close()
    cursor=g.conn.execute('select e.eid, e.capacity, count(a.sid) from attend a, events e where a.eid=%s and e.eid=a.eid group by e.eid',(eid))
    capacity=cursor.fetchone()
    cursor.close()
    if B:
      if cond=='Join':
        cursor=g.conn.execute('select name from students where sid=%s',(sid))
        name=cursor.fetchone()[0]
        cursor.close()
        if capacity[2]<=int(capacity[1]):
          g.conn.execute('INSERT INTO attend (sid, eid, name) VALUES (%s, %s, %s)', [sid, eid, name])
        else:
          txt='List is full for this event.'
          return render_template('test.html',message=txt)
      elif cond=='Leave':
        try:
          g.conn.execute('delete from attend where sid=%s and eid=%s',[sid,eid])
        except:
          txt='There was an issue leaving the list.'
          return render_template('test.html',message=txt)
      return redirect(url_for('eventdetail',eid=eid))
    else:
      txt='You are already in the list.'
      return render_template('test.html',message=txt)
  else:
    return render_template('login.html')

@app.route('/test',methods=['POST','GET'])
def test():
  return render_template('test.html')

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
