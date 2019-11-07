from datetime import datetime as dt
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
    class Post:
        def __init__(self, raw):
            self._raw = raw
            self.pkey = raw[0]
            self.created = int(raw[1])
            self.username = raw[2]
            self.title = raw[3]
            self.content = raw[4]
            self.likes = int(raw[5])
            self.deleted = bool(raw[6])
            self.image = raw[7]

            self._timestamp = dt.utcfromtimestamp(self.created)
            self.date = self._timestamp.strftime('%m/%d/%y')
            self.time = self._timestamp.strftime('%I:%M%p').lower()
 
        def __repr__(self):
            return 'Post(%s, %s, \'%s\', %s likes)' % (self.pkey, self.username, self.title, self.likes)
    
    class User:
        def __init__(self, raw):
            self._raw = raw
            self.username = raw[0]
            self.password = raw[1]
            self.admin = bool(raw[3])

            self.liked_posts = raw[2].split(',')
            if not self.liked_posts[0]: self.liked_posts = []
        
        def __repr__(self):
            if self.admin:
                return 'User(%s, %s, admin)' % (self.username, len(self.liked_posts))
            else:
                return 'User(%s, %s)' % (self.username, len(self.liked_posts))
    
    class Comment:
        def __init__(self, raw):
            self._raw = raw
            self.post_pkey = raw[0]
            self.username = raw[1]
            self.created = int(raw[2])
            self.content = raw[3]
 
            self._timestamp = dt.utcfromtimestamp(self.created)
            self.date = self._timestamp.strftime('%m/%d/%y')
            self.time = self._timestamp.strftime('%I:%M%p').lower()
   
        def __repr__(self):
            return 'Comment(%s, \'%s\', %s)' % (self.username, self.content, self.post_pkey)

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
    def user_add(self, cur, username, password, admin=False):
        hashed = security.generate_password_hash(password)

        query = 'INSERT INTO users VALUES (?, ?, ?, ?)'
        cur.execute(query, (username, hashed, '', admin))

    @with_database
    def user_fetch(self, cur, username):
        query = 'SELECT * FROM users WHERE username=?'
        resp = cur.execute(query, (username,))

        return Forum.User(resp.fetchone())

    @with_database
    def user_validate(self, cur, username, password):
        query = 'SELECT password FROM users WHERE username=?'
        resp = cur.execute(query, (username,))
        results = resp.fetchall()
        if not len(results): return False
        return security.check_password_hash(results[0][0], password)

    @with_database
    def user_exists(self, cur, username):
        query = 'SELECT COUNT(*) FROM users WHERE username=?'
        resp = cur.execute(query, (username,))
        return bool(resp.fetchone()[0])
    
    # OPERATIONS: posts
    @with_database
    def post_add(self, cur, username, title, content, image=None, likes=0):
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

        return post_pkey
    
    @with_database
    def post_fetch(self, cur, post_pkey):
        query = 'SELECT * FROM posts WHERE post_pkey=?'
        resp = cur.execute(query, (post_pkey,))

        return Forum.Post(resp.fetchone())

    @with_database
    def post_gather(self, cur, quantity, deleted=False):
        query = 'SELECT * FROM posts WHERE deleted!=? ORDER BY create_date DESC LIMIT ?'
        resp = cur.execute(query, (not deleted, quantity))
        return [ Forum.Post(a) for a in resp.fetchall() ]

    @with_database
    def post_delete(self, cur, post_pkey, deleted=True):
        query = 'UPDATE posts SET deleted=? WHERE post_pkey=?'
        cur.execute(query, (deleted, post_pkey))
 
    @with_database
    def post_like(self, cur, username, post_pkey):
        liked_posts = self.user_fetch(username).liked_posts

        if post_pkey in liked_posts: return False
        else: liked_posts = ','.join(liked_posts + [post_pkey])

        query = 'UPDATE users SET liked_posts=? WHERE username=?'
        cur.execute(query, (liked_posts, username))

        query = 'UPDATE posts SET likes=likes+1 WHERE post_pkey=?'
        cur.execute(query, (post_pkey,))

        return True

    @with_database
    def post_unlike(self, cur, username, post_pkey):
        liked_posts = self.user_fetch(username).liked_posts

        if not post_pkey in liked_posts: return False
        else: liked_posts = ','.join([a for a in liked_posts if a != post_pkey])

        query = 'UPDATE users SET liked_posts=? WHERE username=?'
        cur.execute(query, (liked_posts, username))

        query = 'UPDATE posts SET likes=likes-1 WHERE post_pkey=?'
        cur.execute(query, (post_pkey,))

        return True


    # OPERATIONS: comments
    @with_database
    def comment_add(self, cur, post_pkey, username, content):
        create_date = int(time.time())
        query = 'INSERT INTO comments VALUES (?, ?, ?, ?, ?)'
        cur.execute(query, (post_pkey, username, create_date, content, false))
    
    @with_database
    def comment_fetch(self, cur, post_pkey, limit=100):
        query = 'SELECT * FROM comments WHERE post_pkey=? ORDER BY create_date DESC LIMIT ?'
        resp = cur.execute(query, (post_pkey, limit))
        return [ Forum.Comment(a) for a in resp.fetchall() ]

# forum_db = Forum('resources/forum.db', schema='resources/schema.sql')
# forum_db.post_add('william', 'no photo this time', 'no photo this time, only words!!! ahahahahah some words that I wrote are neat, right?', image='https://cdn.photographylife.com/wp-content/uploads/2016/06/Brown-Anole.jpg')

# forum_db.post_like('william', 'WIL19110613')
# print(forum_db.post_fetch('WIL19110613'))