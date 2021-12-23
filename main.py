from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
import sqlite3

list_of_questions = [("вам нравятся русские буквы?",), ("вам нравятся латинские буквы?",)]

db = sqlite3.connect(r'test.db')
cur = db.cursor()


cur.execute(
    """CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q1 INTEGER,
    q2 INTEGER )
    """)

cur.execute(
    """CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT
    )""")


cur.execute(
    """CREATE TABLE
    user ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gender TEXT,
    education TEXT,
    age INTEGER )""")

for smth in list_of_questions:
    cur.execute(
        '''INSERT into questions (text) VALUES (?) ''', smth
    )

db.commit()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'  # имя таблицы
    id = db.Column(db.Integer, primary_key=True) # имя колонки = специальный тип (тип данных, первичный ключ)
    gender = db.Column(db.Text)
    education = db.Column(db.Text)
    age = db.Column(db.Integer)


class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)


class Answers(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    q1 = db.Column(db.Integer)
    q2 = db.Column(db.Integer)

@app.route('/')
def base():
    with open("intro.txt", "r", encoding='utf-8') as f:
        content = f.read().split('\n')
    return render_template("base.html", content=content)

@app.route('/questions')
def question_page():
    questions = Questions.query.all() # имя_таблицы.query.взять_все()
    return render_template(
        'questions.html',
        questions=questions
    )


@app.route('/process', methods=['get'])
def answer_process():
    # если пустой запрос, то отправить проходить анкету
    if not request.args:
        return redirect(url_for('question_page'))

    # получаем значения ответов
    gender = request.args.get('gender')
    education = request.args.get('education')
    age = request.args.get('age')

    # записываем в базу
    user = User(
        age=age,
        gender=gender,
        education=education
    )
    db.session.add(user)
    db.session.commit()

    # обновляем user'a, чтобы его ответ записать с таким же id
    db.session.refresh(user)

    # это же делаем с ответом
    q1 = request.args.get('q1')
    q2 = request.args.get('q2')
    answer = Answers(
        id=user.id,
        q1=q1,
        q2=q2
    )
    db.session.add(answer)
    db.session.commit()

    return 'спасибо! за участие'


@app.route('/stats')
def stats():
    # заводим словарь для значений (чтобы не передавать каждое в render_template)
    all_info = {}

    age_stats = db.session.query(
        func.avg(User.age),  # средний возраст AVG(user.age)
        func.min(User.age),  # минимальный возраст MIN(user.age)
        func.max(User.age)  # максимальный возраст MAX(user.age)
    ).one()  # берем один результат (он всего и будет один)

    all_info['age_mean'] = age_stats[0]
    all_info['age_min'] = age_stats[1]
    all_info['age_max'] = age_stats[2]

    # это простой запрос, можно прямо у таблицы спросить
    all_info['total_count'] = User.query.count()  # SELECT COUNT(age) FROM user

    # SELECT AVG(q1) FROM answers
    all_info['q1_mean'] = db.session.query(func.avg(Answers.q1)).one()[0]

    # SELECT q1 FROM answers
    q1_answers = db.session.query(Answers.q1).all()

    # SELECT AVG(q1) FROM answers
    all_info['q2_mean'] = db.session.query(func.avg(Answers.q2)).one()[0]

    # SELECT q1 FROM answers
    q2_answers = db.session.query(Answers.q2).all()

    return render_template('results.html', all_info=all_info)
if __name__ == '__main__':
    app.run()