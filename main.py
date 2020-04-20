from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy #for database connectivity, and required 'mysqlclient' module
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail
# pip install flask, flask-sqlalchemy, mysqlclient, flask-mail

with open('config.json', 'r') as config:
    parameters = json.load(config)['params']

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = parameters['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=parameters['gmail_user_id'],
    MAIL_PASSWORD=parameters['gmail_user_password']
)  # above parameters will be always fixed except username and password

mail = Mail(app)

if parameters['local_server']:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']  # in json->user:password@localhost/databaseName
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    """
    sno, name, email, phone, msg, date :Note- all variables must same as givn in table columns
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(13), unique=True, nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(80), nullable=False)


class Posts(db.Model):
    """
    seno, slug, title, content, date, place :Note- all variables must same as givn in table columns
    """
    seno = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(25), nullable=False)
    title = db.Column(db.String(50), nullable=False)
    tagline = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(13), nullable=False)
    place = db.Column(db.String(20), nullable=False)


@app.route("/")
def home():
    page = request.args.get('page', 1 , type = int) # from get request page variable comes i.e ?page=3
    posts = Posts.query.order_by(Posts.date.desc()).paginate(page = page, per_page = parameters['no_posts_in_home'])
    """     order_by(Posts.date.desc()) arrange posts in descending order acc to date, paginated - create a object of posts for pagination"""
    return render_template('index.html', parametersfortemp = parameters, postsfortemp = posts)# passing json parameters


@app.route("/about")
def about():
    return render_template('/about.html', parametersfortemp = parameters)


@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == parameters['admin_user_id']:
        posts = Posts.query.filter_by().all()
        return render_template('/dashboard.html', parametersfortemp = parameters, posts = posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        if username == parameters['admin_user_id'] and password == parameters['admin_user_password']:
            # set the session variable
            session['user'] = username
            posts = Posts.query.filter_by().all()
            return render_template('/dashboard.html', parametersfortemp = parameters, posts = posts)
    else:
        return render_template('/login.html', parametersfortemp = parameters)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Add entry to the database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('number')
        message = request.form.get('message')

        entry = Contacts(name = name, phone = phone, msg = message, date = datetime.now(), email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,  # email of sender of contact form
                          recipients = [parameters['gmail_user_id']],  # a list of mail who recieve this msg
                          body = message + "\n" + phone  # msg body of mail to be send
                          )
    return render_template('/contact.html', parametersfortemp = parameters)


@app.route("/post/<string:post_slug>", methods = ['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()  # slug should be unique
    return render_template('/post.html', parametersfortemp = parameters, postfortemp = post)


@app.route("/edit/<string:seno>", methods = ['GET', 'POST'])
def edit(seno):
    if 'user' in session and session['user'] == parameters['admin_user_id']:
        if request.method == 'POST':
            """ slug, title, tagline, content, place,"""
            slug = request.form.get('slug') # the parameter is name of element in HTML
            title = request.form.get('title')
            tagline = request.form.get('tagline')
            content = request.form.get('content')
            place = request.form.get('place')

            if seno == '0': # strategy is if seno == 0 a new post will be added
                post = Posts(title=title, slug=slug, tagline=tagline, content=content, place=place, date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(seno = seno).first() # why? seno = seno
                post.title = title
                post.slug = slug
                post.tagline = tagline
                post.content = content
                post.place = place
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+seno)
        post = Posts.query.filter_by(seno = seno).first()
        return render_template('edit.html', parametersfortemp = parameters, post = post, seno = seno)
        # if post contains None, jinja treate it as empty string

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == parameters['admin_user_id']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:seno>")
def delete(seno):
    if 'user' in session and session['user'] == parameters['admin_user_id']:
        post = Posts.query.filter_by(seno = seno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


app.run(debug=True)



























