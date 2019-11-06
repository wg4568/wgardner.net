from werkzeug import security
import sqlite3
import time

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

class Forum:
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
    
    # OPERATIONS: users
    @with_database
    def user_exists(self, cur, username):
        query = 'SELECT COUNT(*) WHERE username=?'
        resp = cur.execute(query, (username,))
        return bool(resp.fetchone()[0])

    @with_database
    def user_create(self, cur, username, password, admin=False):
        hashed = security.generate_password_hash(password)

        query = 'INSERT INTO users VALUES (?, ?, ?, ?)'
        cur.execute(query, (username, hashed, '', admin))
    
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
    
    # OPERATIONS: posts
    @with_database
    def post_create(self, cur, username, title, content, image=None, likes=0):
        pkey_first = username[:3].upper() + time.strftime('%y%m%d')

        query = 'SELECT COUNT(*) FROM posts WHERE post_pkey LIKE ?'
        suffix = cur.execute(query, (pkey_first + '%',)).fetchone()[0]

        post_pkey = pkey_first + str(suffix)
        create_date = int(time.time())

        query = 'INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(query, (
            post_pkey, create_date,
            username, title, content,
            likes, False, image
        ))
    
    @with_database
    def post_delete(self, cur, post_pkey, deleted=True):
        query = 'UPDATE posts SET deleted=? WHERE post_pkey=?'
        cur.execute(query, (deleted, post_pkey))
    
    @with_database
    def post_gather(self, quantity, deleted=False):
        query = 'SELECT * FROM posts WHERE deleted!=? ORDER BY create_date DESC LIMIT ?'
        resp = cur.execute(query, (deleted, quantity))
        return resp.fetchall()
    
    @with_database
    def post_like(self, cur, username, post_pkey):
        query = 'SELECT liked_posts FROM users WHERE username=?'
        resp = cur.execute(query, (username,))

        liked_posts = resp.fetchone()[0].split(',')
        if not liked_posts[0]: liked_posts = []
        if post_pkey in liked_posts: return
        else: liked_posts = ','.join(liked_posts + [post_pkey])

        query = 'UPDATE users SET liked_posts=? WHERE username=?'
        cur.execute(query, (liked_posts, username))

        # query = ''

db = Forum('db.db', schema='resources/schema.sql')
# db.user_create('wg4568', 'password')
# db.post_create('wg4568', 'Cool Post', 'so like I wanna do this and that\nand also coool!')

db.post_like('wg4568', 'WG41911062')