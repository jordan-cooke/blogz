from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'blogz'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    post = db.relationship('Blog', backref='owner')
    
    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['index', 'blog', 'login', 'signup']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route("/")
def index():
    users = User.query.all()
    user_id = request.args.get("user_id")
    if user_id:
        posts = Blog.query.filter_by(owner_id=user_id).all()
        return render_template("selecteduser.html", users=users, posts=posts)
    return render_template("index.html", users=users)

@app.route("/blog")
def blog():
    posts = Blog.query.all()
    post_id = request.args.get("id")
    user_id = request.args.get("user_id")
    users = User.query.all()
    if user_id:
        posts = Blog.query.filter_by(owner_id=user_id).all()
        return render_template("selecteduser.html", posts=posts, users=users)
    if post_id:
        post = Blog.query.get(post_id)
        return render_template("selectedpost.html", post=post, users=users)
    return render_template("blog.html", posts=posts, users=users)

@app.route("/newpost", methods=['POST', 'GET'])
def newpost():
    title_error = ""
    body_error = ""
    if request.method == "POST":
        title = request.form['title']
        body = request.form['body']    
        if title == "":
            title_error = "Please fill in the title."
        if body == "":
            body_error = "Please fill in the body."
        if len(title) > 0 and len(body) > 0:
            owner = User.query.filter_by(username=session['username']).first()
            new_post = Blog(title, body, owner)
            db.session.add(new_post)
            db.session.commit()
            post_url = "/blog?id=" + str(new_post.id)
            return redirect(post_url)
    return render_template("newpost.html", title_error=title_error, body_error=body_error)

@app.route("/login", methods=['POST', 'GET'])
def login():
    username_error = ""
    password_error = ""
    if request.method == 'POST':
        username = request.form['username']
        username = username.strip(" ")
        password = request.form['password']
        password = password.strip(" ")
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect("/newpost") 
        if not user:
            username_error = "Username doesn't exist."
        if user and not check_pw_hash(password, user.pw_hash):
            password_error = "Incorrect password."
    return render_template("login.html", username_error=username_error, password_error=password_error)

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    username_error = ""
    password_error = ""
    verify_error = ""
    if request.method == 'POST':
        username = request.form['username']
        username = username.strip(" ")
        password = request.form['password']
        password = password.strip(" ")
        verify = request.form['verify']
        verify = verify.strip(" ")
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user and len(username) >= 3 and len(password) >= 3 and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        if existing_user:
            username_error = "Username already exists."
        if len(username) < 3:
            username_error = "Username must be more than 2 characters."
        if len(password) < 3:
            password_error = "Password must be more than 2 characters."
        if password != verify:
            verify_error = "Passwords don't match"
    return render_template("signup.html", username_error=username_error, password_error=password_error, verify_error=verify_error)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


if __name__ == '__main__':
    app.run()