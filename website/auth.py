from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import *
from .mail_functions import *
from .policy import policy
from password_strength import PasswordStats
from flask_login import login_user, login_required, logout_user, current_user
from flask_mail import Message
import requests


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        if user:
            if user.activated == False:
                flash('Please verify your email in order to log in for the first time!', category='error')
            elif user.password == None:
                flash('Seems like that email is already connected through google, you can login with google account down here below!', category='error')
            elif check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=remember)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, please try again', category='error')
                return render_template("login.html", user=current_user, entered_email=email)
        else:
            flash('Email does not exist', category='error')
        
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('views.home'))

@auth.route('/activate/<token>', methods=["GET", "POST"])
def activate_account(token):
        if current_user.is_authenticated:
            return render_template("home.html", user=current_user)
        
        user = User.verify_token(token)
        print("Received token:", token)
        
        if user is None:
            flash('That is an invalid or expired token', category='error')
        else:
            verify_email(user)
            flash('Account is now activated, you can login now!', category='success')
            
        return redirect(url_for('auth.login'))
    
@auth.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    
    if request.method == "POST":
        email = request.form.get('email')
        userName = request.form.get('userName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        stats = PasswordStats(password1)
        check_email = User.query.filter_by(email=email).first()
        check_userName = User.query.filter_by(userName=userName).first()
        
        if check_email:
            flash('Email already exists.', category='error')
        elif len(email) < 1:
            flash('Email is too short! must be more than 1 characters', category='error')
        elif check_userName:
            flash('Username already exists.', category='error')
            return render_template("sign_up.html", user=None, entered_email = email)
        elif len(userName) < 2:
            flash('Username must be more than 1 characters', category='error')
            return render_template("sign_up.html", user=None, entered_email = email)
        elif len(userName) > 18:
            flash('Username cannot be more than 18 characters', category='error')
            return render_template("sign_up.html", user=None, entered_email = email)
        elif stats.strength() < 0.2:
            flash("Password not strong enough. Avoid consecutive charcters and easily guessed words.", category='error')
            return render_template("sign_up.html", user=None, entered_email = email)
        elif password1 != password2:
            flash('Passwords don\'t match', category='error')
            return render_template("sign_up.html", user=None, entered_email = email, entered_username = userName)
        else:
            new_user = User(email=email, userName=userName, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            send_activation_email(new_user)
            flash('Account created, please verify your email in order to log in!', category='success')
            return redirect(url_for('auth.login'))
            
    return render_template("sign_up.html", user=None)

@auth.route('/forgot-password', methods=["GET", "POST"])
def forgot_request():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    
    if request.method == 'POST':
        email = request.form.get('forgotPasswordEmail')
        user = User.query.filter_by(email=email).first()
        if user:
            if user.activated == False:
                flash('Please first activate your account via the link we sent to your email.', category='error')
            elif user.password == None:
                flash('This user is connected through google, no need for password in order to login just click "Continue with google".', category='error')
            else:
                send_reset_email(user)
                flash('Password reset email sent!', category='success')
        else:
            flash('there is no account with that email. Sign up first.', category='error') 
            
    return redirect(url_for('auth.login'))
    
@auth.route('/reset-password/<token>', methods=["GET", "POST"])
def forgot_password(token):
        if current_user.is_authenticated:
            return render_template("home.html", user=current_user)
        
        user = User.verify_reset_password_token(token)
        print("Received token:", token)
        
        if user is None:
            flash('That is an invalid or expired token', category='error')
            return redirect(url_for('auth.login'))
        
        if request.method == "POST":
            password1 = request.form.get('password')
            password2 = request.form.get('confirm-password')
            stats = PasswordStats(password1)  
            if stats.strength() < 0.2:
                flash("Password not strong enough. Avoid consecutive charcters and easily guessed words.", category='error')
            elif password1 != password2:
                flash('Passwords don\'t match', category='error')
            else:
                user.password = generate_password_hash(password1, method='sha256')
                user.get_token()
                db.session.commit()
                flash('Your password has been updated! You are now able to log in', category='success')
                return redirect(url_for('auth.login'))
        return render_template('reset_password.html', user=None)
    
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Google OAuth>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@app.route("/auth/google")
def login():
    if current_user.is_authenticated:
        return render_template("home.html", user=current_user)
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    try:
        flow.fetch_token(authorization_response=request.url)

        if not session["state"] == request.args["state"]:
            abort(500)  # State does not match!

        credentials = flow.credentials
        request_session = requests.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        session["google_id"] = id_info.get("sub")
        session["name"] = id_info.get("name")
        session["email"] = id_info.get("email")  # Store the user's email

        user = User.query.filter_by(email=session["email"]).first()
        if user is None:
            return redirect(url_for('choose_username'))
        else:
            flash('Logged in successfully!', category='success')
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
    except:
        return render_template('errors/403.html', user = None)

@app.route("/choose-username", methods=["GET", "POST"])
def choose_username():
        if current_user.is_authenticated:
            return render_template("errors/403.html", user=current_user)
        
        try:
            user = User.query.filter_by(email=session["email"]).first()
        except:
            return render_template('errors/403.html', user = None)
        
        if user is None:
            if request.method == "POST":
                userName = request.form.get('userName')
                check_userName = User.query.filter_by(userName=userName).first()

                if check_userName:
                    flash('Username already exists.', category='error')
                    return render_template("choose_username.html", email=session["email"], user=None)
                elif len(userName) < 2:
                    flash('Username must be more than 1 characters', category='error')
                    return render_template("choose_username.html", email=session["email"], user=None)
                elif len(userName) > 18:
                    flash('Username cannot be more than 18 characters', category='error')
                    return render_template("choose_username.html", email=session["email"], user=None)
                else:
                    new_user = User(email=session["email"], userName=userName, password=None, activated=True)
                    db.session.add(new_user)
                    db.session.commit()
                    flash('Account created!', category='success')
                    login_user(new_user, remember=True)
                    return redirect(url_for('views.home')) 
        else:
            return render_template('errors/403.html', user = None)
        
        return render_template("choose_username.html", email=session["email"], user=None)