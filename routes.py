import re
from flask import render_template, url_for, request, session, redirect
from markupsafe import escape
from config import app, db
from models import Subjects, Users, Answers, Topics, Questions, ChangeReq
from utils import *

def get_topics_and_subjects():
    subjects = Subjects.query.order_by(Subjects.name).all()
    topics = {}
    for subject in subjects:
        topic = Topics.query.filter_by(subject_id=subject.id).all()
        topics[subject.name] = topic
    return subjects, topics

def init_db(with_example_data=False):
    app.app_context().push()
    db.create_all()
    Subjects.query.delete()
    Topics.query.delete()
    Users.query.delete()
    Questions.query.delete()
    if with_example_data:
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

@app.route('/', strict_slashes=False)
def index_page():
    if "username" not in session:
        return login_page()
    subjects, topics = get_topics_and_subjects()
    active = {"index": "active"}
    return render_template("index.html", subjects=subjects, topics=topics, active=active, user=session["username"], admin=session["admin"])

@app.route('/<subject>/<topic>', strict_slashes=False)
def topic_page(subject, topic):
    if "username" not in session:
        session["redirect_to"] = url_for("topic_page", subject=subject, topic=topic)
        return login_page()
    subject = Subjects.query.filter_by(name=subject).first()
    topic = Topics.query.filter_by(title=topic, subject_id=subject.id).first()
    subjects, topics = get_topics_and_subjects()
    active = {subject.name: "active"}
    return render_template("topic.html", akt_topic=topic, akt_subject=subject, active=active, subjects=subjects, topics=topics, admin=session["admin"])

@app.route('/<subject>/<topic>/question', strict_slashes=False, methods=['GET', 'POST'])
def question_page(subject, topic):
    if "username" not in session:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        question = escape(request.form["question"])
        user = Users.query.filter_by(username=session["username"]).first()
        topic = Topics.query.filter_by(title=topic).first()
        question = Questions(user_id=user.id, topic_id=topic.id, content=question)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for("topic_page", subject=subject, topic=topic.title))
    else:
        return redirect(url_for("topic_page", subject=subject, topic=topic))

@app.route('/search', strict_slashes=False, methods=['GET', 'POST'])
def search_page():
    if "username" not in session:
        return login_page()
    if request.method == "GET":
        query = escape(request.args.get("query"))
        res_topics = Topics.query.filter(Topics.title.contains(query)).all()
        res_topics.extend(Topics.query.filter(Topics.content.contains(query)).all())
        res_topics = list(set(res_topics)) #Delete duplicates

        subjects, topics = get_topics_and_subjects()
        active = {}
        subject_map = {}
        for subject in subjects:
            subject_map[subject.id] = subject.name

        return render_template("search.html", results=res_topics, subject_map=subject_map, active=active, subjects=subjects, topics=topics, query=query, admin=session["admin"])
    else:
        return redirect(url_for("index_page"))

#####################
# Account
#####################
@app.route('/login', methods=['GET', 'POST'], strict_slashes=False)
def login_page():
    if request.method == "POST":
        username = escape(request.form["username"])
        password = escape(request.form["password"])
        user = Users.query.filter_by(username=username).first()
        if user:
            if verify_password(user.password, password):
                session["name"] = user.name
                session["username"] = user.username
                session["role"] = user.role
                session["admin"] = user.role in ["admin", "owner"]
                session["id"] = user.id
                redirect_to = session.pop("redirect_to", url_for("index_page"))
                return redirect(redirect_to)
            else:
                return render_template("account/login.html", error="password")
        else:
            return render_template("account/login.html", error="username")
    else:
        return render_template("account/login.html", error="")

@app.route('/register', methods=['GET', 'POST'], strict_slashes=False)
def register_page():
    if request.method == "POST":
        name = escape(request.form["name"])
        username = escape(request.form["username"])
        email = escape(request.form["email"])
        password = escape(request.form["password"])
        hashed_password = hash_password(password)
        role = escape("default")
        if not re.match(username_pattern, username):
            return render_template("account/register.html", error="username", name=name, email=email, username=username)
        if not re.match(password_pattern, password):
            return render_template("account/register.html", error="password", name=name, email=email, username=username)
        if not re.match(email_pattern, email):
            return render_template("account/register.html", error="email", name=name, email=email, username=username)
        if not re.match(name_pattern, name):
            return render_template("account/register.html", error="name", name=name, email=email, username=username)
        if Users.query.filter_by(username=username).first():
            return render_template("account/register.html", error="username", name=name, email=email, username=username)
        user = Users(name=name, username=username, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        user = Users.query.filter_by(username=username).first()
        if user and verify_password(user.password, password):
            session["name"] = user.name
            session["username"] = user.username
            session["role"] = user.role
            session["admin"] = user.role in ["admin", "owner"]
            session["id"] = user.id
            return redirect(url_for("index_page"))
        return redirect(url_for("login_page"))
    else:
        return render_template("account/register.html", error="", name="", email="", username="")

@app.route('/logout', strict_slashes=False)
def logout_page():
    session.pop("name", None)
    session.pop("username", None)
    session.pop("role", None)
    return redirect(url_for("index_page"))

#####################
# Administration
#####################
@app.route('/administration', strict_slashes=False)
def administration_page():
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/index.html", subjects=subjects, topics=topics, user=session["username"], admin=session["admin"], active=active)

@app.route('/administration/subjects', strict_slashes=False)
def administration_subject_page():
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/subjects.html", subjects=subjects, topics=topics, user=session["username"], admin=session["admin"], active=active)

@app.route('/administration/users', strict_slashes=False)
def administration_user_page():
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    users = Users.query.all()
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/users.html", subjects=subjects, topics=topics, users=users, user=session, admin=session["admin"], active=active, role=session["role"])

@app.route('/administration/users/delete/<user_id>', strict_slashes=False)
def administration_user_delete_page(user_id):
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    if not Users.query.filter_by(id=user_id).first():
        return redirect(url_for("administration_user_page"))
    if Users.query.filter_by(id=user_id).first().id == session["id"]:
        return redirect(url_for("administration_user_page"))
    if Users.query.filter_by(id=user_id).first().role in ["admin", "owner"]:
        if session["role"] != "owner":
            return redirect(url_for("administration_user_page"))
    Users.query.filter_by(id=user_id).delete()
    db.session.commit()
    return redirect(url_for("administration_user_page"))

@app.route('/administration/users/edit/<user_id>', strict_slashes=False, methods=['GET', 'POST'])
def administration_user_edit_page(user_id):
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    user = Users.query.filter_by(id=user_id).first()
    if not user:
        return redirect(url_for("administration_user_page"))
    if request.method == "POST":
        role = escape(request.form["role"])
        if not role in ["default", "admin", "owner"]:
            return redirect(url_for("administration_user_page"))
        user.role = role
        db.session.commit()
        return redirect(url_for("administration_user_page"))
    else:
        return redirect(url_for("administration_user_page"))

@app.route('/administration/topics', strict_slashes=False)
def administration_topic_page():
    if "username" not in session or not session["admin"]:
        return redirect(url_for("index_page"))
    users = Users.query.all()
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/topics.html", subjects=subjects, topics=topics, users=users, user=session["username"], admin=session["admin"], active=active)