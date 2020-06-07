from flask import g
import psycopg2
from psycopg2.extras import DictCursor


def connect_db():
    conn = psycopg2.connect('postgres://xphcnlgkphmfox:1c2dacb722ea2b08e1bdbf075653c36e0285380274e5b4bdea2a390ee840615d@ec2-107-21-102-221.compute-1.amazonaws.com:5432/dbcau377ljol5l', cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql


def get_db():
    db = connect_db()
    if not hasattr(g, "postgres_db_conn"):
        g.postgres_db_conn = db[0]
    
    if not hasattr(g, "postgres_db_cur"):
        g.postgres_db_cur = db[1]
    
    return g.postgres_db_cur


def init_db():
    db = connect_db()

    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()
    db[0].close()

def init_admin():
    db = connect_db()

    db[1].execute('update users set admin = True where name = %s', ('admin', ))

    db[1].close()
    db[0].close()
