from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import Bootstrap5
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired


app = Flask(__name__, template_folder="templates")
app.secret_key = 'dev-fallback-key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bootstrap5 = Bootstrap5(app)


class QuizFileForm(FlaskForm):
    file = FileField("Select JSON file", validators=[DataRequired()])
    submit = SubmitField("Start Quiz")


@app.route("/", methods=["POST", "GET"])
def index():
    form = QuizFileForm()
    return render_template("index.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
