from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os

import ctypes

from .db import get_db
from . import add_deadline

bp = Blueprint("blog", __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}

libc = ctypes.CDLL(None, use_errno=True)


@bp.route("/")
@add_deadline(30, ["GET"])
def index():
    """Show all the posts, most recent first."""
    
    db = get_db()
    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("blog/index.html", posts=posts)

@bp.route("/<int:id>")
@add_deadline(5, methods=["GET"])
def get_post(id):
    """Show a single post."""
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")
    
    return render_template("blog/index.html", posts=[post])


@bp.route("/create", methods=("GET", "POST"))
@add_deadline(100, ["POST"])
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            if g.user is None:
                db.execute(
                    "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                    (title, body, 1),
                )
            else:
                db.execute(
                    "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                    (title, body, g.user["id"]),
                )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def count_words(filename):
    text = open(filename, "r") 
    d = dict() 
    
    for line in text: 
        line = line.strip()  
        line = line.lower() 
        words = line.split(" ") 

        for word in words: 
            if word in d: 
                d[word] = d[word] + 1
            else: 
                d[word] = 1
    return d

@bp.route('/docount', methods=['GET', 'POST'])
@add_deadline(1500, methods=["POST"])
def do_count():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            
            # do some processing of the file
            word_dict = count_words(os.path.join(os.getcwd(), UPLOAD_FOLDER, filename))
            s = dict(sorted(word_dict.items(), key=lambda item: item[1]))
            l = [(k, v) for (k, v) in s.items()]
            popular_word, file_count = l[0]

            os.remove(os.path.join(UPLOAD_FOLDER, filename))

            return render_template("blog/success.html", word=popular_word, count=file_count)
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''