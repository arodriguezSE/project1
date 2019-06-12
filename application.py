import os

from flask import Flask, session,render_template,request,redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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


@app.route("/")
def index():
    #return "Project 1: TODO"
    return(render_template("index.html"))

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