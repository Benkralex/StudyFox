import re
import urllib

from flask import render_template, url_for, request, session, redirect, send_from_directory
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
    if not subject:
        return redirect(url_for("index_page"))
    topic = Topics.query.filter_by(title=topic, subject_id=subject.id).first()
    subjects, topics = get_topics_and_subjects()
    active = {subject.name: "active"}
    questions = Questions.query.filter_by(topic_id=topic.id).all()
    answers = {}
    indexed_to_delete = []
    for question in questions:
        if question.answer_id:
            answers[question.id] = Answers.query.filter_by(id=question.answer_id).first()
        elif not question.user_id == session["id"]:
            indexed_to_delete.append(question.id)
    for i in indexed_to_delete:
        questions = [q for q in questions if q.id != i]
    users = {}
    for user in Users.query.all():
        users[user.id] = user.username
    return render_template("topic.html", html_content=escapedhtml_to_html(topic.content), act_topic=topic, act_subject=subject, active=active, subjects=subjects, topics=topics, admin=session["admin"], questions=questions, answers=answers, users=users)

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
        if len(Users.query.all()) == 0:
            role = escape("owner")
        else:
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
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/index.html", subjects=subjects, topics=topics, user=session["username"], admin=session["admin"], active=active)

@app.route('/administration/subjects', strict_slashes=False)
def administration_subject_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    topic_count = {}
    for s in Subjects.query.all():
        topic_count[s.id] = 0
    for t in Topics.query.all():
        topic_count[t.subject_id] += 1
    active = {"admin": "active"}
    return render_template("administration/subjects.html", subjects=subjects, topics=topics, user=session, admin=session["admin"], active=active, topic_count=topic_count)

@app.route('/administration/subjects/delete/<s_id>', strict_slashes=False)
def administration_subject_delete_page(s_id):
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    if (not Subjects.query.filter_by(id=s_id).first()) or session["role"] != "owner":
        return redirect(url_for("administration_subject_page"))
    for t in Topics.query.filter_by(subject_id=s_id).all():
        for q in Questions.query.filter_by(topic_id=t.id).all():
            Answers.query.filter_by(id=q.answer_id).delete()
            Questions.query.filter_by(id=q.id).delete()
    Topics.query.filter_by(subject_id=s_id).delete()
    Subjects.query.filter_by(id=s_id).delete()
    db.session.commit()
    return redirect(url_for("administration_subject_page"))

@app.route('/administration/subjects/create', strict_slashes=False, methods=['GET', 'POST'])
def administration_subject_create_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    if request.method == "POST":
        name = escape(request.form["name"])
        description = escape(request.form["description"])
        if not name:
            return redirect(url_for("administration_subject_page"))
        if not description:
            description = ""
        subject = Subjects(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        return redirect(url_for("administration_subject_page"))
    else:
        return redirect(url_for("administration_subject_page"))

@app.route('/administration/users', strict_slashes=False)
def administration_user_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    users = Users.query.all()
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/users.html", subjects=subjects, topics=topics, users=users, user=session, admin=session["admin"], active=active, role=session["role"])

@app.route('/administration/users/delete/<user_id>', strict_slashes=False)
def administration_user_delete_page(user_id):
    if "username" not in session:
        return login_page()
    if not session["admin"]:
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
    if "username" not in session:
        return login_page()
    if not session["admin"]:
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
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    users = Users.query.all()
    subjects, topics = get_topics_and_subjects()
    topic_list = Topics.query.all()
    subject_id_map = {}
    for s in subjects:
        subject_id_map[s.id] = s.name
    active = {"admin": "active"}
    return render_template("administration/topics.html", subject_id_map=subject_id_map, topic_list=topic_list, subjects=subjects, topics=topics, users=users, user=session, admin=session["admin"], active=active)

@app.route('/administration/topics/delete/<t_id>', strict_slashes=False)
def administration_topic_delete_page(t_id):
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    if (not Topics.query.filter_by(id=t_id).first()) or session["role"] != "owner":
        return redirect(url_for("administration_subject_page"))
    for t in Topics.query.filter_by(id=t_id).all():
        for q in Questions.query.filter_by(topic_id=t.id).all():
            Answers.query.filter_by(id=q.answer_id).delete()
            Questions.query.filter_by(id=q.id).delete()
    Topics.query.filter_by(id=t_id).delete()
    db.session.commit()
    return redirect(url_for("administration_topic_page"))

@app.route('/administration/topics/new', strict_slashes=False, methods=['POST'])
def administration_new_topic_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    if request.method == "POST":
        content = escape(request.form["content"])
        title = escape(request.form["title"])
        try:
            subject = int(request.form["subject"])
        except ValueError:
            return redirect(url_for("administration_topic_page"))
        if not content or not title or not subject:
            return redirect(url_for("administration_topic_page"))
        if not Subjects.query.filter_by(id=subject).first():
            return redirect(url_for("administration_topic_page"))
        if Topics.query.filter_by(title=title, subject_id=subject).first():
            return redirect(url_for("administration_topic_page"))
        db.session.add(Topics(title=title, subject_id=subject, content=content))
        db.session.commit()
        return redirect(url_for("administration_topic_page"))
    else:
        return redirect(url_for("administration_topic_page"))

@app.route('/administration/upload-file', strict_slashes=False)
def administration_upload_file():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    return render_template("administration/upload_file.html", subjects=subjects, topics=topics, active=active, admin=session["admin"], user=session)

@app.route('/administration/editor', strict_slashes=False)
def editor_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    imgs = []
    for img in os.listdir("img"):
        imgs.append(img)
    return render_template("administration/editor.html", subjects=subjects, topics=topics, active=active, admin=session["admin"], imgs=imgs)

@app.route('/administration/gallery', strict_slashes=False)
def gallery_page():
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    subjects, topics = get_topics_and_subjects()
    active = {"admin": "active"}
    imgs = []
    for img in os.listdir("img"):
        imgs.append(img)
    return render_template("administration/gallery.html", subjects=subjects, topics=topics, active=active, admin=session["admin"], imgs=imgs)

@app.route('/administration/gallery/delete/<img>', strict_slashes=False)
def gallery_delete_page(img):
    if "username" not in session:
        return login_page()
    if not session["admin"]:
        return redirect(url_for("index_page"))
    if not os.path.exists("img/" + img):
        return redirect(url_for("gallery_page"))
    os.remove("img/" + img)
    return redirect(url_for("gallery_page"))

#####################
# Files and Links
#####################
@app.route('/link/<path:link>', strict_slashes=False)
def link_page(link):
    if "username" not in session:
        return login_page()
    decoded_link = urllib.parse.unquote(link)
    return render_template("link.html", link=decoded_link)

@app.route('/img/<image>', strict_slashes=False)
def img_page(image):
    if "username" not in session:
        return login_page()
    #decoded_image = urllib.parse.unquote(image)
    return send_from_directory("img", image)

@app.route('/upload/img', strict_slashes=False, methods=['POST', 'GET'])
def upload_page():
    if "username" not in session or not session["admin"]:
        return login_page()
    if request.method == "POST":
        file = request.files["file"]
        filename = escape(request.form["filename"])
        fileextension = file.filename.split(".")[-1]
        if fileextension not in ["png", "jpg", "jpeg", "gif"]:
            return redirect(url_for("administration_upload_file"))
        if file:
            file.save("img/" + filename + "_" + session["username"] + "." + fileextension)
    return redirect(url_for("administration_upload_file"))