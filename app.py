from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
from datetime import datetime, timedelta
from openpyxl import Workbook
from io import BytesIO
from models import db, WordBook, Word, Translation
from translation_service import translate_text

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

@app.route('/export_excel')
def export_excel():
    wb = Workbook()
    ws = wb.active
    ws.append(['单词', '词性', '翻译'])
    
    book = WordBook.query.filter_by(name=current_book).first()
    if book:
        for word in Word.query.filter_by(book_id=book.id).all():
            for trans in word.translations:
                ws.append([word.word, trans.pos, trans.translation])
    
    try:
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return Response(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-disposition': 'attachment; filename=vocabulary.xlsx'}
        )
    except Exception as e:
        print(f'导出表格文件时出现错误: {e}')
        return Response('导出表格文件时出现错误', status=500)

# 新增计数器
word_submission_count = 0

@app.route('/add', methods=['POST'])
def add_word():
    global word_submission_count
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
    
    # 每次提交单词，计数器加1
    word_submission_count += 1
    
    # 每5次单词提交备份一次数据库
    if word_submission_count % 5 == 0:
        backup_database()
        word_submission_count = 0
    
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
    # 如果删除的是当前单词本或只剩两个单词本，切换到默认单词本
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

# 数据库自动备份函数
def backup_database():
    """自动备份数据库文件
    
    每当用户提交5次单词后，系统会自动调用此函数进行数据库备份
    备份文件会以时间戳命名，存储在instance目录下
    """
    import shutil
    from datetime import datetime
    
    # 获取当前时间戳作为文件名的一部分
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 备份文件名格式：words_backup_年月日时分秒.db
    backup_filename = f'instance/words_backup_{timestamp}.db'
    
    # 使用shutil.copyfile复制数据库文件
    shutil.copyfile('instance/words.db', backup_filename)
    
    print(f'数据库备份成功，备份文件名为: {backup_filename}')
    # 备份文件存储在instance目录下，可以在需要时用于恢复数据

@app.route('/translate', methods=['POST'])
def translate():
    word = request.form.get('word')
    if not word:
        return jsonify({'success': False, 'error': '未提供单词'})
    
    result = translate_text(word)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)