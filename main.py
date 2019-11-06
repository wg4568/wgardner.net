from flask import Flask, render_template, session, request, redirect, abort
import requests
import bs4
import json
import database
import os

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

        if not price_el or not change_el: abort(400)

        price = float(price_el['content'].replace(',',''))
        change = float(change_el['content'].replace('%',''))

        return json.dumps({'price': price, 'change': change})
    else:
        abort(405)

# SITE SECTION: Live forum demo
@app.route('/demos/forum')
def demos_forum():
    return ''

# Launch the application
app.run(
    host=config['host'],
    port=config['port'],
    debug=config['debug']
)