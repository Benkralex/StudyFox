import hashlib
import os

from flask import Flask, render_template, url_for, send_from_directory, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape

app = Flask(__name__)

app.secret_key = '82236§%$q7oc1351!§"452749281/&(65q2'

app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'
app.config['SERVER_NAME'] = 'localhost:5000'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'studyfox-logo.png', mimetype='image/png')

class Subjects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=True)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Topics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

class ChangeReq(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

def create_db():
    db.create_all()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return salt.hex() + hashed_password

def verify_password(stored_hash: str, password: str) -> bool:
    salt = bytes.fromhex(stored_hash[:32])
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    return stored_hash[32:] == hashed_password

def get_topics_and_subjects():
    subjects = Subjects.query.order_by(Subjects.name).all()
    topics = {}
    for subject in subjects:
        topic = Topics.query.filter_by(subject_id=subject.id).all()
        topics[subject.name] = topic
    return subjects, topics

@app.route('/', strict_slashes=False)
def index():
    if "username" not in session:
        return login()
    subjects, topics = get_topics_and_subjects()
    return render_template("index.html", subjects=subjects, topics=topics, user=session["username"])

@app.route('/<subject>/<topic>', strict_slashes=False)
def topic(subject, topic):
    if "username" not in session:
        session["redirect_to"] = url_for("topic", subject=subject, topic=topic)
        return login()
    subject = Subjects.query.filter_by(name=subject).first()
    topic = Topics.query.filter_by(title=topic, subject_id=subject.id).first()
    subjects, topics = get_topics_and_subjects()
    return render_template("topic.html", akt_topic=topic, akt_subject=subject, subjects=subjects, topics=topics)

@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login():
    if request.method == "POST":
        username = escape(request.form["username"])
        password = escape(request.form["password"])
        user = Users.query.filter_by(username=username).first()
        if user:
            if verify_password(user.password, password):
                session["name"] = user.name
                session["username"] = user.username
                session["role"] = user.role
                redirect_to = session.pop("redirect_to", url_for("index"))
                return redirect(redirect_to)
            else:
                return render_template("login.html", error="password")
        else:
            return render_template("login.html", error="username")
    else:
        return render_template("login.html", error="")

@app.route('/register', methods=['GET', 'POST'], strict_slashes=False)
def register():
    if request.method == "POST":
        name = escape(request.form["name"])
        username = escape(request.form["username"])
        email = escape(request.form["email"])
        password = escape(request.form["password"])
        hashed_password = hash_password(password)
        role = escape("default")
        if Users.query.filter_by(username=username).first():
            return render_template("register.html", error="username", name=name, email=email, username=username)
        user = Users(name=name, username=username, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        user = Users.query.filter_by(username=username).first()
        if user and verify_password(user.password, password):
            session["name"] = user.name
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("index"))
        return redirect(url_for("login"))
    else:
        return render_template("register.html", error="")

@app.route('/logout', strict_slashes=False)
def logout():
    session.pop("name", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("index"))

@app.route('/<subject>/<topic>/question', strict_slashes=False, methods=['GET', 'POST'])
def question(subject, topic):
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        question = escape(request.form["question"])
        user = Users.query.filter_by(username=session["username"]).first()
        topic = Topics.query.filter_by(title=topic).first()
        question = Questions(user_id=user.id, topic_id=topic.id, content=question)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for("topic", subject=subject, topic=topic.title))
    else:
        return render_template("question.html", subject=subject, topic=topic)

@app.route('/search', strict_slashes=False, methods=['GET', 'POST'])
def search():
    if "username" not in session:
        return login()
    if request.method == "GET":
        query = escape(request.args.get("query"))
        res_topics = Topics.query.filter(Topics.title.contains(query)).all()
        res_topics.extend(Topics.query.filter(Topics.content.contains(query)).all())
        subjects = Subjects.query.all()
        subject_map = {}
        for subject in subjects:
            subject_map[subject.id] = subject.name
        subjects, topics = get_topics_and_subjects()
        return render_template("search.html", results=res_topics, subject_map=subject_map, subjects=subjects, topics=topics, query=query)
    else:
        return redirect(url_for("index"))

if __name__ == '__main__':
    app.app_context().push()
    url_for('static', filename='style.css')
    url_for('static', filename='form.css')
    url_for('static', filename='topic.css')
    url_for('static', filename='studyfox-logo.png')
    #TEST-DATA START
    create_db()
    Subjects.query.delete()
    Topics.query.delete()
    Users.query.delete()
    Questions.query.delete()
    db.session.add(Subjects(name='Mathe', description='Mathe ist die Lehre von Nummern, Formen und Mustern.'))
    db.session.add(Topics(title='Potenzen', subject_id=1, content='Potenzen sind die Multiplikation einer Zahl mit sich selbst.'))
    db.session.add(Topics(title='Wurzeln', subject_id=1, content='Wurzeln sind die Umkehrung von Potenzen.'))
    db.session.add(Topics(title='Brüche', subject_id=1, content='Brüche sind Zahlen, die nicht ganzzahlig sind.'))
    db.session.add(Topics(title='Gleichungen', subject_id=1, content='Gleichungen sind mathematische Aussagen, die auf ihre Richtigkeit überprüft werden können.'))
    db.session.add(Subjects(name='Deutsch', description='Deutsch ist die Lehre der deutschen Sprache.'))
    db.session.add(Topics(title='Grammatik', subject_id=2, content='Grammatik ist die Lehre von der Struktur einer Sprache.'))
    db.session.add(Topics(title='Rechtschreibung', subject_id=2, content='Rechtschreibung ist die Lehre der korrekten Schreibweise von Wörtern.'))
    db.session.add(Topics(title='Interpunktion', subject_id=2, content='Interpunktion ist die Lehre der korrekten Zeichensetzung.'))
    db.session.commit()
    #TEST-DATA END
    app.run(debug=True)