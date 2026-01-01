from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import Bootstrap5
from wtforms import FileField, SubmitField, RadioField
from flask_wtf.file import FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired
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

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bootstrap5 = Bootstrap5(app)


# ===== MODELS =====
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


class UserAnswer(db.Model):
    __tablename__ = "user_answers"
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    selected_option_id = db.Column(
        db.Integer, db.ForeignKey("options.id"), nullable=False
    )


# ===== HELPERS =====
def validate_quiz_json(data):
    if not isinstance(data, dict):
        raise ValueError("Root must be an object")

    if "title" not in data:
        raise ValueError("Quiz must have a title")

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


def create_quiz_form(quiz):
    class DynamicQuizForm(FlaskForm):
        submit = SubmitField("Submit Quiz")

    for q in quiz.questions:
        choices = [(str(opt.id), opt.text) for opt in q.options]
        setattr(
            DynamicQuizForm,
            f"question_{q.id}",
            RadioField(
                q.text, choices=choices, validators=[DataRequired()], coerce=str
            ),
        )

    return DynamicQuizForm()


# ===== ROUTES =====
@app.route("/", methods=["POST", "GET"])
def index():
    form = QuizFileForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            validate_quiz_json(data)
            quiz_id = save_quiz_to_db(data)
            flash(f"Quiz uploaded successfully! ID={quiz_id}", "success")
        except json.JSONDecodeError:
            flash("Invalid JSON file", "danger")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Unexpected error: {str(e)}", "danger")
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    return render_template("index.html", form=form)


@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
def quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = create_quiz_form(quiz)

    if form.validate_on_submit():
        score = 0
        total = len(quiz.questions)

        for q in quiz.questions:
            field_name = f"question_{q.id}"
            selected_option_id = int(form[field_name].data)
            option = Option.query.get(selected_option_id)
            if option.is_correct:
                score += 1
            answer = UserAnswer(
                quiz_id=quiz.id, question_id=q.id, selected_option_id=selected_option_id
            )
            db.session.add(answer)

        db.session.commit()
        flash(f"You scored {score}/{total}!", "success")
        return render_template("result.html", quiz=quiz, score=score, total=total)

    return render_template("quiz.html", form=form, quiz=quiz)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
