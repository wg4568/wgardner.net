CREATE TABLE users (
    username        TEXT NOT NULL UNIQUE,
    password        TEXT NOT NULL,
    admin           INTEGER DEFAULT 0
);

CREATE TABLE posts (
    post_pkey       PRIMARY KEY,
    create_date     INTEGER NOT NULL,
    username        TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    likes           INTEGER DEFAULT 0,
    image           TEXT
);