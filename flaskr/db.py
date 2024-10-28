import sqlite3

import click
from flask import current_app
from flask import g
from faker import Faker


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    
def fill_db():
    """Fill db with fake data."""
    fake = Faker()

    conn = get_db()
    cursor = conn.cursor()

    # Create sample users
    users = []
    for _ in range(10):  # Create 10 users
        username = fake.user_name()
        password = fake.password()
        cursor.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, password))
        print("un: " + str(username) + "pw: " + str(password))
        users.append(cursor.lastrowid)

    # Create 500 sample posts
    for _ in range(500):
        author_id = fake.random.choice(users)
        title = fake.sentence()
        body = fake.paragraph()
        cursor.execute('INSERT INTO post (author_id, title, body) VALUES (?, ?, ?)', (author_id, title, body))
    
    conn.commit()
    conn.close()



@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")
    fill_db()
    click.echo("Filled the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
