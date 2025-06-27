from app import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    profile = db.relationship('Profile', backref='user', uselist=False)