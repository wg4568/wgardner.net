from flask import Flask, render_template, 
import json
import database

# Initialize globals
app = Flask(__name__)
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
    return 'Hello, world!'

# Launch the application
app.run(
    host=config['host'],
    port=config['port'],
    debug=config['debug']
)