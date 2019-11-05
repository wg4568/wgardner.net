from flask import Flask, render_template, session, request, redirect, abort
import json
import database
import os

# Initialize globals
app = Flask(__name__)
pages = [ a.split('.')[0] for a in os.listdir('templates/site') ]
db = database.Database('database.db', schema='resources/schema.sql')

# Load configuration from file
with open('resources/config.json') as f:
    config = json.load(f)

# Generate secure secret key for session encryption
if config['debug']:
    app.secret_key = 'super_secret_debug_key'
    db.debug = True
else:
    app.secret_key = secrets.token_hex(config['secret_length'])

@app.route('/')
def index():
    return redirect('/site/home')

@app.route('/site/<page>')
def site(page):
    if page not in pages: abort(404)
    else: return render_template('site/%s.html' % page)

# Launch the application
app.run(
    host=config['host'],
    port=config['port'],
    debug=config['debug']
)