from app import db

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
