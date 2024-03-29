import os
import requests

from flask import Flask, session,render_template,request,redirect,url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import login_required


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/",methods=["GET","POST"])
@login_required
def index():
    if request.method =="GET":
        return(render_template("index.html"))
    else:
        isbn=request.form.get("isbn")
        author=request.form.get("author")
        title=request.form.get("title")

        matches = db.execute("SELECT * FROM books WHERE LOWER(author) LIKE LOWER(:author) AND LOWER(title) LIKE LOWER(:title) AND LOWER(isbn) LIKE LOWER(:isbn)", {"author": "%"+author+"%","title": "%"+title+"%","isbn": isbn+"%" }).fetchall()
        #matches = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
        return(render_template("matches.html", matches = matches,numMatches=len(matches)))
@app.route("/<string:isbn>")
def book(isbn):
    book = db.execute("SELECT * FROM books WHERE LOWER(isbn) = LOWER(:isbn)", {"isbn": isbn }).fetchone()
    if book is None:
        return render_template("error.html", message="No such book")
    else:
        reviews = db.execute("SELECT * FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id", {"book_id": book.isbn}).fetchall()
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "bz6TldmQRGULiQQtkASw", "isbns": book.isbn})
        if res.status_code==200:
            resJ=res.json()
            rating = resJ["books"][0]["average_rating"]
        else:
            rating=None

        return render_template("book.html",book=book,reviews=reviews,rating=rating)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method =="GET":
        return(render_template("register.html"))
    else:
        username=request.form.get("username")
        password = request.form.get("password")


        usertaken = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        if usertaken is None:
            resp = db.execute("INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id",
            {"username": username, "password": password}).fetchone()
            db.commit()
            #row= dict(resp)
            #userId=row["id"]
            #print(userId)
            #print(resp.id)
            session.clear()
            session["user_id"] = resp.id
            return redirect("/")

        else:
            return("username taken")
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method =="GET":
        return(render_template("login.html"))
    else:
        username=request.form.get("username")
        password = request.form.get("password")


        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        print(type(user))
        if user is None:
            return("username doesn't exist")
        elif user.password != password:
            return("incorrect password")

        else:
            session.clear()
            session["user_id"] = user.id
            return redirect("/")
@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect("/")

@app.route("/<string:isbn>/review", methods=["GET","POST"])
def review(isbn):
    if request.method =="GET":
        row = db.execute("SELECT title FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
        return(render_template("review.html",isbn=isbn,title=row.title))
    else:
        rating=request.form.get("rating")
        text=request.form.get("text")
        user = session.get("user_id")
        reviewMade = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :isbn", {"user_id":user, "isbn": isbn}).fetchone()
        if reviewMade is None:
            db.execute("INSERT INTO reviews (user_id, rating,review_text,book_id) VALUES (:user, :rating, :text, :isbn)",
            {"user": user, "rating": rating, "text": text, "isbn": isbn})
            db.commit()
            url="/"+isbn
            return redirect(url)
        else:
            return("review already made")
