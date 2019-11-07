# requires faker library not in requirements.txt
# $ pip install faker
from faker import Faker
from database import Forum
import json
import requests
import random
import bs4

with open('resources/secrets.json') as f:
    secrets = json.load(f)

forum_db = Forum('resources/forum.db', schema='resources/schema.sql')
fake = Faker()

usernames = []
post_pkeys = []

N_USERS = 25
N_POSTS = N_USERS * 5
N_COMMENTS = N_POSTS * 12
N_LIKES = N_POSTS * 25

for _ in range(N_USERS):
    username = fake.user_name()
    forum_db.user_add(username, secrets['faker_password'])
    usernames.append(username)
    print('User', _, username)

for _ in range(N_POSTS):
    title_len = random.randint(2, 5)
    body_len = random.randint(2, 5)
    username = random.choice(usernames)
    title = ' '.join([ a.capitalize() for a in fake.words(nb=title_len, unique=True) ])
    content = ' '.join(fake.paragraphs(nb=body_len))
    image = None
    if random.random() < 0.7:
        url = 'https://pixabay.com/images/search/' + title.split()[0]
        resp = requests.get(url)
        soup = bs4.BeautifulSoup(resp.text, features='html.parser')

        imgs = soup.findAll('img', {'srcset': True})
        try: image = random.choice(imgs)['src']
        except IndexError: pass

    pkey = forum_db.post_add(username, title, content, image=image)
    post_pkeys.append(pkey)
    print('Post', _, username, title, image)

for _ in range(N_COMMENTS):
    body_len = random.randint(1, 3)
    pkey = random.choice(post_pkeys)
    username = random.choice(usernames)
    content = ' '.join(fake.paragraphs(nb=body_len))
    forum_db.comment_add(pkey, username, content)
    print('Comment', _, username, pkey)

for _ in range(N_LIKES):
    username = random.choice(usernames)
    pkey = random.choice(post_pkeys)
    forum_db.post_like(username, pkey)
    print('Like', _, username, pkey)

print(usernames)
print(post_pkeys)