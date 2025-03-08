from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime, timedelta
import csv
from io import StringIO
from models import db, WordBook, Word, Translation

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///words.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

current_book = '默认单词本'

class WordEntry:
    def __init__(self, word, translations):
        self.word = word
        self.translations = translations
        self.hidden_until = None

@app.route('/')
def index():
    global current_book
    book_name = request.args.get('book', current_book)
    current_book = book_name
    book = WordBook.query.filter_by(name=book_name).first()
    if not book:
        book = WordBook(name=book_name)
        db.session.add(book)
        db.session.commit()
    
    words = Word.query.filter_by(book_id=book.id).all()
    filtered_data = [WordEntry(word.word, [{'pos': t.pos, 'translation': t.translation} for t in word.translations]) 
                    for word in words if not word.hidden_until or word.hidden_until < datetime.now()]
    
    return render_template('index.html', 
                         word_data=filtered_data,
                         current_book=book_name,
                         books=[b.name for b in WordBook.query.all()])

@app.route('/export_db')
def export_db():
    return Response(
        open('instance/words.db', 'rb').read(),
        mimetype='application/octet-stream',
        headers={'Content-disposition': 'attachment; filename=words.db'}
    )

@app.route('/export_csv')
def export_csv():
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['单词', '词性', '翻译'])
    
    book = WordBook.query.filter_by(name=current_book).first()
    if book:
        for word in Word.query.filter_by(book_id=book.id).all():
            for trans in word.translations:
                writer.writerow([word.word, trans.pos, trans.translation])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=vocabulary.csv"}
    )

@app.route('/add', methods=['POST'])
def add_word():
    word = request.form['word']
    pos = request.form['pos']
    translation = request.form['translation']
    book = WordBook.query.filter_by(name=current_book).first()
    if not book:
        book = WordBook(name=current_book)
        db.session.add(book)
        db.session.commit()
    
    existing_word = Word.query.filter_by(word=word, book_id=book.id).first()
    if existing_word:
        existing_trans = Translation.query.filter_by(word_id=existing_word.id, pos=pos).first()
        if existing_trans:
            existing_trans.translation = translation
        else:
            new_trans = Translation(pos=pos, translation=translation, word_id=existing_word.id)
            db.session.add(new_trans)
        existing_word.hidden_until = None
    else:
        new_word = Word(word=word, book_id=book.id)
        db.session.add(new_word)
        db.session.commit()
        new_trans = Translation(pos=pos, translation=translation, word_id=new_word.id)
        db.session.add(new_trans)
    db.session.commit()
    return redirect(url_for('index', book=current_book))

@app.route('/add_book', methods=['POST'])
def add_book():
    book_name = request.form['book_name']
    existing_book = WordBook.query.filter_by(name=book_name).first()
    if not existing_book:
        new_book = WordBook(name=book_name)
        db.session.add(new_book)
        db.session.commit()
    return redirect(url_for('index', book=current_book))

@app.route('/delete_book', methods=['POST'])
def delete_book():
    global current_book
    book_name = request.form['book_name']
    if book_name == '默认单词本':
        return "不能删除默认单词本", 400
    book = WordBook.query.filter_by(name=book_name).first()
    if not book:
        return "单词本不存在", 404
    # 先删除该单词本下的所有单词
    for word in Word.query.filter_by(book_id=book.id).all():
        Translation.query.filter_by(word_id=word.id).delete()
        db.session.delete(word)
    # 再删除单词本
    if book_name == current_book or WordBook.query.count() == 2:
        current_book = '默认单词本'
    # 先删除该单词本下的所有单词
    for word in Word.query.filter_by(book_id=book.id).all():
        Translation.query.filter_by(word_id=word.id).delete()
        db.session.delete(word)
    # 最后删除单词本
    db.session.delete(book)
    db.session.commit()
    # 跳转到默认单词本
    return redirect(url_for('index', book='默认单词本'))

@app.route('/delete_word/<word>', methods=['POST'])
def delete_word(word):
    book = WordBook.query.filter_by(name=current_book).first()
    if book:
        word_to_delete = Word.query.filter_by(word=word, book_id=book.id).first()
        if word_to_delete:
            Translation.query.filter_by(word_id=word_to_delete.id).delete()
            db.session.delete(word_to_delete)
            db.session.commit()
            return '', 204
    return redirect(url_for('index', book=current_book))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)