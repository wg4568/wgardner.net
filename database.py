from werkzeug import security
import sqlite3
import datetime

# Wrapper that provides repetitive cursor functionality
def with_database(func):
    def wrapped(self, *args, **kwargs):
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        resp = func(self, cur, *args, **kwargs)
        conn.commit()
        conn.close()
        return resp
    return wrapped

class Database:
    def __init__(self, path, schema='schema.sql', debug=False):
        self.path = path
        self.schema = open(schema, 'r').read()
        self.debug = debug
 
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        try: cur.executescript(self.schema)
        except sqlite3.OperationalError: pass

        conn.commit()
        conn.close()
    
    @with_database
    def user_exists(self, cur, username):
        query = 'SELECT COUNT(*) WHERE username=?'
        resp = cur.execute(query, (username,))
        return bool(resp.fetchone()[0])

    @with_database
    def user_create(self, cur, username, password, admin=False):
        hashed = security.generate_password_hash(password)

        query = 'INSERT INTO users VALUES (?, ?, ?)'
        cur.execute(query, (username, hashed, admin))
    
    @with_database
    def user_validate(self, cur, username, password):
        query = 'SELECT password FROM users WHERE username=?'
        resp = cur.execute(query, (username,))
        results = resp.fetchall()
        if not len(results): return False
        return security.check_password_hash(results[0][0], password)
    
    @with_database
    def user_admin(self, cur, username):
        query = 'SELECT COUNT(*) FROM users WHERE username=? AND admin=1'
        resp = cur.execute(query, (username,))
        return bool(resp.fetchone()[0])