from flask import url_for
from .models import User
from . import db, app, mail
from flask_mail import Message

def send_activation_email(user):
    token = user.get_token()
    msg = Message('Account Activation', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To activate your account, visit the following link: {url_for('auth.activate_account', token=token, _external=True)}.
    If you did not register for this account then simply ignore this email and no changes will be made.
    '''
        
    mail.send(msg)

def verify_email(user):
    user.activated = True
    user.get_token()
    db.session.commit()
    
def send_reset_email(user):
    token = user.get_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])

    msg.body = f'''To reset your password, visit the following link: {url_for('auth.forgot_password', token=token, _external=True)}.
    PLEASE NOTICE:THE LINK WILL EXPIRE IN 5 MINUTES.
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)