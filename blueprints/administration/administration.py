from flask import Blueprint, render_template

administration = Blueprint('administration', __name__, template_folder='templates')

@administration.route('/', strict_slashes=False)
def index():
    return render_template("index.html")

@administration.route('/users', strict_slashes=False)
def users():
    return render_template("users.html")

@administration.route('/users/<username>', strict_slashes=False)
def user(username):
    return render_template("user.html")

@administration.route('/users/<username>/edit', strict_slashes=False)
def edit_user(username):
    return render_template("edit_user.html")

@administration.route('subjects', strict_slashes=False)
def subjects():
    return render_template("subjects.html")

@administration.route('subjects/<subject>', strict_slashes=False)
def subject(subject):
    return render_template("subject.html")

@administration.route('subjects/<subject>/edit', strict_slashes=False)
def edit_subject(subject):
    return render_template("edit_subject.html")

@administration.route('subjects/<subject>/topics', strict_slashes=False)
def topics(subject):
    return render_template("topics.html")

@administration.route('subjects/<subject>/topics/<topic>', strict_slashes=False)
def topic(subject, topic):
    return render_template("topic.html")

@administration.route('subjects/<subject>/topics/<topic>/edit', strict_slashes=False)
def edit_topic(subject, topic):
    return render_template("edit_topic.html")

@administration.route('subjects/<subject>/topics/<topic>/questions', strict_slashes=False)
def questions(subject, topic):
    return render_template("questions.html")

@administration.route('subjects/<subject>/topics/<topic>/questions/<question>', strict_slashes=False)
def question(subject, topic, question):
    return render_template("question.html")
