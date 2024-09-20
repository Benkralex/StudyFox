import os

from flask import Flask, render_template, url_for, send_from_directory, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = '82236§%$q7oc1351!§"452749281/&(65q2'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

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

@app.route('/')
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    subjects = Subjects.query.order_by(Subjects.name).all()
    return render_template("index.html", subjects=subjects)

@app.route('/<subject>')
def subject(subject):
    if "username" not in session:
        return redirect(url_for("login"))
    subject_id = Subjects.query.filter_by(name=subject).first()
    subject_id = subject_id.id
    topics = Topics.query.filter_by(subject_id=subject_id).order_by(Topics.title).all()
    return render_template("subject.html", subject=subject, topics=topics)

@app.route('/<subject>/<topic>')
def topic(subject, topic):
    if "username" not in session:
        return redirect(url_for("login"))
    topic = Topics.query.filter_by(title=topic).first()
    return render_template("topic.html", topic=topic, subject=subject)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user and user.password == password:
            session["name"] = user.name
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Username or password is incorrect.")
    else:
        return render_template("login.html", error="")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = "default"
        if Users.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already exists.")
        user = Users(name=name, username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    else:
        return render_template("register.html", error="")

@app.route('/logout')
def logout():
    session.pop("name", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.app_context().push()
    #TEST-DATA START
    #create_db()
    Subjects.query.delete()
    Topics.query.delete()
    db.session.add(Subjects(name='Mathe', description='Mate ist die Lehre von Nummern, Formen und Mustern.'))
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