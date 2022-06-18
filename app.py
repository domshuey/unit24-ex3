from crypt import methods
from http.client import UNAUTHORIZED
from flask import Flask, redirect, render_template, flash, session, get_flashed_messages
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import connect
from flask_bcrypt import Bcrypt
from models import User, connect_db, db, Feedback
from forms import FeedbackForm, UserForm, LoginForm
from werkzeug.exceptions import Unauthorized


app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


bcrypt = Bcrypt()
connect_db(app)


@app.route('/')
def redirect_to_register():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = UserForm()

    if 'user' in session:
        return redirect(f'/users/{session["user"]}')

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/secret')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = LoginForm()

    if 'user' in session:
        return redirect(f'/users/{session["user"]}')

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)

        if user:
            session['user'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            flash('Incorrect username/password. Please try again.')
            return redirect('/login')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    flash('BYE!')
    session.pop('user')
    return redirect('/')

@app.route('/secret')
def welcome():
    if 'user' not in session:
        return render_template('secret.html')
    else:
        return redirect('/login')

@app.route('/users/<username>')
def show_user_info(username):
    user = User.query.get_or_404(username)
    feedback = Feedback.query.filter_by(username = user.username).all()

    if username == session['user']:
        return render_template('user.html', user=user, feedback=feedback)
    else:
        flash('You need to be logged in to view your user information')
        return redirect('/login')

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    user = User.query.get_or_404(username)
    if session['user'] == username and 'user' in session:
        db.session.delete(user)
        db.session.commit()
        session.pop('user')
        return redirect('/register')
    else:
        raise Unauthorized()

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    user = User.query.get_or_404(username)
    form = FeedbackForm()

    if form.validate_on_submit():
        if session['user'] == username and 'user' in session:
            title = form.title.data
            content = form.content.data
            new_feedback = Feedback(title = title, content = content, username=user.username)
            db.session.add(new_feedback)
            db.session.commit()
            return redirect(f'/users/{username}')
        else:
            raise Unauthorized()

    if session['user'] != username or 'user' not in session:
        raise Unauthorized()
    else:
        return render_template('addFeedback.html', user=user, form=form)
    

@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    feedback = Feedback.query.get(id)
    form = FeedbackForm(obj=feedback)

    if session['user'] != feedback.username or 'user' not in session:
        raise Unauthorized()

    if form.validate_on_submit():
        if session['user'] == feedback.username and 'user' in session:
            feedback.title = form.title.data
            feedback.content = form.content.data
            db.session.commit()

            return redirect(f'/users/{feedback.username}')
    
    return render_template('updateFeedback.html', form=form, feedback=feedback)

@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    feedback = Feedback.query.get(id)
    
    if session['user'] != feedback.username or 'user' not in session:
        raise Unauthorized()

    db.session.delete(feedback)
    db.session.commit()
    return redirect('/login')
    
