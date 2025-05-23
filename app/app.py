from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# データベース設定
basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "quiz.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# モデル定義
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Quiz {self.id}: {self.question[:50]}...>'

# ルート定義
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        
        if not question or not answer:
            flash('問題と答えの両方を入力してください。', 'error')
            return render_template('create.html')
        
        try:
            new_quiz = Quiz(question=question, answer=answer)
            db.session.add(new_quiz)
            db.session.commit()
            flash('クイズが保存されました！', 'success')
            return redirect(url_for('create'))
        except Exception as e:
            flash(f'保存エラー: {str(e)}', 'error')
            return render_template('create.html')
    
    return render_template('create.html')

@app.route('/quiz')
def quiz():
    quizzes = Quiz.query.all()
    if not quizzes:
        flash('問題がありません。まず問題を作成してください。', 'info')
        return redirect(url_for('index'))
    
    quiz = random.choice(quizzes)
    return render_template('quiz.html', quiz=quiz)

@app.route('/check_answer', methods=['POST'])
def check_answer():
    quiz_id = request.form.get('id', type=int)
    user_answer = request.form.get('user_answer', '').strip()
    
    if not quiz_id or not user_answer:
        flash('不正なアクセスです。', 'error')
        return redirect(url_for('quiz'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    is_correct = (user_answer == quiz.answer)
    
    return render_template('check_answer.html', 
                         quiz=quiz, 
                         user_answer=user_answer, 
                         is_correct=is_correct)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    quizzes = Quiz.query.order_by(Quiz.id).all()
    edit_quiz = None
    
    if request.method == 'POST' and 'load_id' in request.form:
        load_id = request.form.get('load_id', type=int)
        if load_id:
            edit_quiz = Quiz.query.get(load_id)
            if not edit_quiz:
                flash('指定したIDの問題は見つかりませんでした。', 'error')
    
    return render_template('edit.html', quizzes=quizzes, edit_quiz=edit_quiz)

@app.route('/update', methods=['POST'])
def update():
    quiz_id = request.form.get('id', type=int)
    action = request.form.get('action', '')
    
    if not quiz_id:
        flash('IDが不正です。', 'error')
        return redirect(url_for('edit'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        if action == '修正':
            question = request.form.get('question', '').strip()
            answer = request.form.get('answer', '').strip()
            
            if not question or not answer:
                flash('問題と答えは必ず入力してください。', 'error')
                return redirect(url_for('edit'))
            
            quiz.question = question
            quiz.answer = answer
            db.session.commit()
            flash('修正が完了しました。', 'success')
            
        elif action == '削除':
            db.session.delete(quiz)
            db.session.commit()
            flash('削除が完了しました。', 'success')
            
        else:
            flash('不正な操作です。', 'error')
            
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
    
    return redirect(url_for('edit'))

# アプリケーション起動時にデータベースを作成
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)