from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import Bootstrap5
from wtforms import FileField, SubmitField
from flask_wtf.file import FileRequired, FileAllowed
from werkzeug.utils import secure_filename
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__, template_folder="templates", static_folder="static", static_url_path="/"
)
app.secret_key = "dev-fallback-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config.update(
    UPLOAD_FOLDER=os.path.join(BASE_DIR, "uploads"),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2MB limit
)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bootstrap5 = Bootstrap5(app)


class QuizFileForm(FlaskForm):
    file = FileField(
        "Select JSON file",
        validators=[
            FileRequired(),
            FileAllowed(["json"], message="Only JSON files are allowed."),
        ],
    )
    submit = SubmitField("Start Quiz")


class Quiz(db.Model):
    __tablename__ = "quiz"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)
    questions = db.relationship(
        "Question", backref="quiz", cascade="all, delete-orphan", lazy=True
    )


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options = db.relationship(
        "Option", backref="question", cascade="all, delete-orphan", lazy=True
    )


class Option(db.Model):
    __tablename__ = "options"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)


def validate_quiz_json(data):
    if not isinstance(data, dict):
        raise ValueError("Root must be an object")

    if "questions" not in data or not isinstance(data["questions"], list):
        raise ValueError("questions must be a list")

    for i, q in enumerate(data["questions"], start=1):
        if "question" not in q:
            raise ValueError(f"Question {i}: missing 'question'")

        if "options" not in q or len(q["options"]) < 2:
            raise ValueError(f"Question {i}: at least 2 options required")

        if "answer" not in q:
            raise ValueError(f"Question {i}: missing 'answer'")

        if not isinstance(q["answer"], int):
            raise ValueError(f"Question {i}: answer must be an integer")

        if q["answer"] >= len(q["options"]):
            raise ValueError(f"Question {i}: answer index out of range")


def save_quiz_to_db(data):
    quiz = Quiz(title=data["title"], time_limit=data.get("time_limit"))

    for q in data["questions"]:
        question = Question(text=q["question"])

        for idx, opt in enumerate(q["options"]):
            option = Option(text=opt, is_correct=(idx == q["answer"]))
            question.options.append(option)

        quiz.questions.append(question)

    db.session.add(quiz)
    db.session.commit()

    return quiz.id


@app.route("/", methods=["POST", "GET"])
def index():
    form = QuizFileForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)  # secure filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)  # save file to upload path
            # check the JSON file
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # check the JSON file structure
            validate_quiz_json(data)
            # save to the database
            quiz_id = save_quiz_to_db(data)
            flash(f"Quiz uploaded successfully! ID={quiz_id}", "success")
        except json.JSONDecodeError:
            flash("Invalid JSON file", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    return render_template("index.html", form=form)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
