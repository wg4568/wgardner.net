CREATE TABLE users (
    username        TEXT NOT NULL UNIQUE,
    password        TEXT NOT NULL,
    liked_posts     TEXT NOT NULL,
    admin           INTEGER DEFAULT 0
);

CREATE TABLE posts (
    post_pkey       TEXT NOT NULL UNIQUE,
    create_date     INTEGER NOT NULL,
    username        TEXT NOT NULL,pos
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    likes           INTEGER NOT NULL,
    deleted         INTEGER NOT NULL,
    image           TEXT
);

CREATE TABLE comments (
    post_pkey       TEXT NOT NULL,
    username        TEXT NOT NULL,
    create_date     INTEGER NOT NULL,
    content         TEXT
);