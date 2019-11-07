from flask import Flask, render_template, session, request, redirect, abort
import requests
import bs4
import json
import database
import os
import sqlite3

# Render html using template file
def render_site_template(template, **kwargs):
    page = template.split('.')[-2].split('/')[-1]
    page_title = page.capitalize()
    content = render_template(template, page=page, **kwargs)
    return render_template(
        'site/template.html', title=page_title,
        page=page, content=content,  **kwargs)

# Initialize globals
app = Flask(__name__)
forum_db = database.Forum('resources/forum.db', schema='resources/schema.sql')
pages = [ a.split('.')[0] for a in os.listdir('templates/site/') ]

# Load configuration from file
with open('resources/config.json') as f:
    config = json.load(f)

# Generate secure secret key for session encryption
if config['debug']:
    app.secret_key = 'super_secret_debug_key'
    forum_db.debug = True

    try: forum_db.user_add('william', 'password', admin=True)
    except sqlite3.IntegrityError: pass
else:
    app.secret_key = secrets.token_hex(config['secret_length'])

# SITE SECTION: static frontend site
@app.route('/')
def index():
    return redirect('/site/about')

@app.route('/site/<page>')
def site(page):
    if page not in pages: abort(404)
    else: return render_site_template('site/%s.html' % page)

# SITE SECTION: Stock checker live demo
@app.route('/demos/stocks', methods=['GET', 'POST'])
def demos_stocks():
    if request.method == 'GET':
        return render_template('demos/stocks.html')
    elif request.method == 'POST':
        code = request.values.get('code')
        if not code: abort(400)
        
        resp = requests.get('https://www.marketwatch.com/investing/stock/%s' % code)
        soup = bs4.BeautifulSoup(resp.text)

        price_el = soup.find('meta', {'name': 'price'})
        change_el = soup.find('meta', {'name': 'priceChangePercent'})
        name_el = soup.find('meta', {'name': 'name'})

        if not price_el or not change_el or not name_el: abort(400)

        price = float(price_el['content'].replace(',',''))
        change = float(change_el['content'].replace('%',''))
        name = name_el['content']

        return json.dumps({'price': price, 'change': change, 'name': name})
    else:
        abort(405)

# SITE SECTION: Live forum demo
def forum_require_auth(func):
    def wrapper(*args, **kwargs):
        if session['forum_logged_in']:
            return func(*args, **kwargs)
        else:
            return redirect('/demos/forum/login')
    wrapper.__name__ = func.__name__
    return wrapper

def render_forum_template(template, **kwargs):
    page = template.split('.')[-2].split('/')[-1]
    page_title = page.capitalize()
    content = render_template(template, page=page, **kwargs)
    return render_template(
        '/demos/forum/template.html',
        title=page_title,
        page=page,
        content=content,
        **kwargs
    )

@app.before_request
def before_request():
    if 'logged_in' not in session:
        session['forum_logged_in'] = False
        session['forum_username'] = None

@app.route('/demos/forum/login', methods=['GET', 'POST'])
def demos_forum_login():
    if request.method == 'GET':
        return render_template('/demos/forum/login.html')
    elif request.method == 'POST':
        username = request.values.get('username')
        password = request.values.get('password')

        if forum_db.user_validate(username, password):
            session['forum_logged_in'] = True
            session['forum_username'] = username
            return redirect('/demos/forum')
        else:
            return redirect('/demos/forum/login?msg=1')
    else:
        abort(405)

@app.route('/demos/forum/logout', methods=['GET'])
def demos_forum_logout():
    session['forum_logged_in'] = False
    session['forum_username'] = None
    return redirect('/demos/forum/login')

@app.route('/demos/forum/signup', methods=['GET', 'POST'])
def demos_forum_signup():
    if request.method == 'GET':
        return render_template('/demos/forum/signup.html')
    elif request.method == 'POST':
        username = request.values.get('username')
        password = request.values.get('password')
        password2 = request.values.get('password2')

        if password != password2: return redirect('/demos/forum/signup?msg=2')
        if forum_db.user_exists(username): return redirect('/demos/forum/signup?msg=1')

        forum_db.user_add(username, password)
        return redirect('/demos/forum/login?msg=3')
    else:
        abort(405)

@app.route('/demos/forum', methods=['GET', 'POST'])
@forum_require_auth
def demos_forum():
    if request.method == 'GET':
        posts = forum_db.post_gather(config['demos']['forum']['max_posts'], comments=True)
        user = forum_db.user_fetch(session['forum_username'])
        return render_forum_template(
            '/demos/forum/home.html',
            username=session['forum_username'],
            posts=posts,
            user=user
        )
    elif request.method == 'POST':
        username = session['forum_username']
        title = request.values.get('title')
        content = request.values.get('content')
        image = request.values.get('image')
        if not image: image = None

        pkey = forum_db.post_add(username, title, content, image=image)
        return redirect('/demos/forum/post/' + pkey)
    else:
        abort(405)

@app.route('/demos/forum/post/<pkey>', methods=['GET', 'POST'])
@forum_require_auth
def demos_forum_post(pkey):
    if request.method == 'GET':
        post = forum_db.post_fetch(pkey)
        user = forum_db.user_fetch(session['forum_username'])
        max_comments = config['demos']['forum']['max_comments']
        return render_forum_template(
            '/demos/forum/post.html',
            username=session['forum_username'],
            comments=forum_db.comment_fetch(pkey, limit=max_comments),
            post=post, user=user
        )
    elif request.method == 'POST':
        username = session['forum_username']
        content = request.values.get('comment')
        forum_db.comment_add(pkey, username, content)
        return redirect('/demos/forum/post/' + pkey)
    else:
        abort(405)

@app.route('/demos/forum/post/<pkey>/like', methods=['POST'])
@forum_require_auth
def demos_forum_post_like(pkey):
    forum_db.post_like(session['forum_username'], pkey)
    return 'ok'

@app.route('/demos/forum/post/<pkey>/unlike', methods=['POST'])
@forum_require_auth
def demos_forum_post_unlike(pkey):
    forum_db.post_unlike(session['forum_username'], pkey)
    return 'ok'

@app.route('/demos/forum/user/<username>', methods=['GET'])
@forum_require_auth
def demos_forum_user(username):
    if request.method == 'GET':
        return render_forum_template(
            '/demos/forum/user.html',
            username=session['forum_username']
        )
    else:
        abort(405)

# Launch the application
app.run(
    host=config['host'],
    port=config['port'],
    debug=config['debug']
)