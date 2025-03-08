from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class WordBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    words = db.relationship('Word', backref='book', lazy=True)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('word_book.id'), nullable=False)
    translations = db.relationship('Translation', backref='word', lazy=True)
    hidden_until = db.Column(db.DateTime)

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pos = db.Column(db.String(20), nullable=False)
    translation = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(20), default='manual')
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)