from pytz import timezone
from. import db, app
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import TimestampSigner

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10000))
    text = db.Column(db.String(110))
    data = db.Column(db.String(10000))
    author = db.Column(db.String(150))
    sent_by = db.Column(db.String(150))
    
    def get_current_datetime():
        return datetime.now(timezone('Asia/Jerusalem')).replace(microsecond=0)
    
    date = db.Column(db.DateTime(timezone=True), default=get_current_datetime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    

    def __init__(self, name, text, data, author ,user_id, sent_by):
        self.name = name
        self.text = text
        self.data = data
        self.user_id = user_id
        self.author = author
        self.sent_by = sent_by

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    userName = db.Column(db.String(150), unique=True, nullable=False)
    activated = db.Column(db.Boolean, default=False) 
    files = db.relationship('File', backref='user', foreign_keys='File.user_id', lazy=True)
    
    def get_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})
    
    @staticmethod
    def verify_reset_password_token(token, max_age=300):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=max_age)['user_id']
            print(user_id)
        except:
            return None
        return User.query.get(user_id)
    
    @staticmethod
    def verify_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
            print(user_id)
        except:
            return None
        return User.query.get(user_id)