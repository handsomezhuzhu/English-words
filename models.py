from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# 初始化SQLAlchemy对象
db = SQLAlchemy()

class WordBook(db.Model):
    """单词本模型
    
    用于存储不同的单词本信息，每个单词本可以包含多个单词
    """
    id = db.Column(db.Integer, primary_key=True)  # 单词本ID，主键
    name = db.Column(db.String(100), unique=True, nullable=False)  # 单词本名称，唯一且不能为空
    words = db.relationship('Word', backref='book', lazy=True)  # 与Word模型的一对多关系

class Word(db.Model):
    """单词模型
    
    用于存储单词信息，每个单词属于一个单词本，可以有多个翻译
    """
    id = db.Column(db.Integer, primary_key=True)  # 单词ID，主键
    word = db.Column(db.String(100), nullable=False)  # 单词内容，不能为空
    book_id = db.Column(db.Integer, db.ForeignKey('word_book.id'), nullable=False)  # 所属单词本ID，外键
    translations = db.relationship('Translation', backref='word', lazy=True)  # 与Translation模型的一对多关系
    hidden_until = db.Column(db.DateTime)  # 单词隐藏截止时间，用于记忆功能

class Translation(db.Model):
    """翻译模型
    
    用于存储单词的翻译信息，包括词性和翻译内容
    每个单词可以有多个不同词性的翻译
    """
    id = db.Column(db.Integer, primary_key=True)  # 翻译ID，主键
    pos = db.Column(db.String(20), nullable=False)  # 词性，不能为空
    translation = db.Column(db.String(200), nullable=False)  # 翻译内容，不能为空
    source = db.Column(db.String(20), default='manual')  # 翻译来源，默认为手动输入
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)  # 所属单词ID，外键