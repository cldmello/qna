import os
from flask import Flask, render_template, request, session, redirect, url_for, g
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def get_current_user():
    res = None
    if 'user' in session:
        user = session['user']
    
        db = get_db()
        cur = db.execute('select id, name, password, expert, admin from users where name = ?', [user])
        res = cur.fetchone()
    
    return res

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    cur = db.execute('''select questions.id as question_id, questions.question_text, 
                        askers.name as asker, experts.name as expert from questions 
                        join users as askers on askers.id = questions.asked_by_id 
                        join users as experts on experts.id = questions.expert_id 
                        where questions.answer_text is not null''')
    questions = cur.fetchall()
    return render_template('home.html', user=user, questions=questions)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        cur = db.execute('select id from users where name = ?', [request.form['name']])
        user = cur.fetchone()

        if user:  # User exists
            return render_template('register.html', user=user, error="User already exists!")

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('insert into users (name, password, expert, admin) values (?, ?, ?, ?)', [request.form['name'], hashed_password, '0', '0'])
        db.commit()
        session['user'] = request.form['name']
        return redirect(url_for('index'))
    
    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        cur = db.execute('select id, name, password from users where name = ?', [name])
        users = cur.fetchone()

        if users:

            if check_password_hash(users['password'], password):
                session['user'] = users['name']
                return redirect(url_for('index'))
            else:
                error = 'Password incorrect!'
        else:
            error = 'Username incorrect!'

    return render_template('login.html', user=user, error=error)

@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()
    db = get_db()
    cur = db.execute('''select questions.answer_text, questions.question_text, 
                        askers.name as asker, experts.name as expert from questions 
                        join users as askers on askers.id = questions.asked_by_id 
                        join users as experts on experts.id = questions.expert_id 
                        where questions.id = ?''', [question_id])
    question = cur.fetchone()
    return render_template('question.html', user=user, question=question)

@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['expert'] == 0:
        return redirect(url_for('index'))
    db = get_db()

    if request.method == 'POST':
        db.execute('update questions set answer_text = ? where id = ?', [request.form['answer'], question_id])
        db.commit()
        return redirect(url_for('unanswered'))
    
    cur = db.execute('select id, question_text from questions where id = ?', [question_id])
    question = cur.fetchone()
    return render_template('answer.html', user=user, question=question)

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    db = get_db()

    if request.method == 'POST':
        db.execute('insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)', [request.form['question'], user['id'], request.form['expert']])
        db.commit()
        return redirect(url_for('index'))
    getexperts = db.execute('select id, name from users where expert = 1')
    experts = getexperts.fetchall()

    return render_template('ask.html', user=user, experts=experts)

@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if user['expert'] == 0:
        return redirect(url_for('index'))

    db = get_db()
    bank = db.execute('''select questions.id, questions.question_text, users.name 
                         from questions join users on users.id = questions.asked_by_id 
                         where questions.answer_text is null and questions.expert_id = ?''', [user['id']])
    questions = bank.fetchall()

    return render_template('unanswered.html', user=user, questions=questions)

@app.route('/users')
def users():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    if user['admin'] == 0:
        return redirect(url_for('index'))

    db = get_db()
    users = db.execute('select id, name, expert, admin from users')
    allusers = users.fetchall()

    return render_template('users.html', user=user, users=allusers)

@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('update users set expert = 1 where id = ?', [user_id])
    db.commit()
    return redirect(url_for('users'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)