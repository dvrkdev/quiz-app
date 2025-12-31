from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from flask_bootstrap import Bootstrap5
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired, ValidationError
import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder="templates")
app.secret_key = "dev-fallback-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config.update(
    UPLOAD_FOLDER=os.path.join(BASE_DIR, "uploads"),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2MB limit
)


db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bootstrap5 = Bootstrap5(app)


class QuizFileForm(FlaskForm):
    file = FileField("Select JSON file", validators=[DataRequired()])
    submit = SubmitField("Start Quiz")

    def validate_file(self, field):
        filename = field.data.filename
        if not re.match(r"^.*\.json$", filename, re.IGNORECASE):
            raise ValidationError("Only JSON files are allowed.")


@app.route("/", methods=["POST", "GET"])
def index():
    form = QuizFileForm()
    if form.validate_on_submit():
        # validation SUCCESS
        pass
    return render_template("index.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
