# quiz-app

A simple Flask-based quiz application that allows uploading quizzes via JSON files, storing them in a database, and taking quizzes dynamically with automatic scoring.  

## Features

- Upload quiz questions as JSON files.
- Validate JSON structure before saving to the database.
- Store quizzes, questions, and options in SQLite via SQLAlchemy.
- Dynamically generate quiz forms with Flask-WTF.
- Track user answers and show results with scores.
- CSRF protection and secure file uploads.
- Bootstrap 5 UI for responsive and clean design.
- Separate dev dependencies for linting and formatting templates.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/dvrkdev/quiz-app.git
    cd quiz-app
    ````

2. Create a virtual environment and activate it:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/Mac
    .venv\Scripts\activate     # Windows
    ```

3. Install production dependencies:

    ```bash
    pip install -r requirements/common.txt
    ```

4. (Optional) Install development dependencies:

    ```bash
    pip install -r requirements/dev.txt
    ```

## Usage

1. Start the Flask development server:

    ```bash
    python app.py
    ```

2. Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000)

3. Upload a quiz JSON file using the form on the home page.

4. After upload, you will see the quiz page where you can take the quiz and view your score.

## JSON Quiz Format

The uploaded JSON file should follow this structure:

```json
{
  "title": "Python Basics Quiz",
  "time_limit": 10,
  "questions": [
    {
      "question": "Which symbols are used to define a list in Python?",
      "options": ["()", "{}", "[]", "<>"],
      "answer": 2
    },
    {
      "question": "What does print(type(5)) output?",
      "options": ["str", "int", "float", "bool"],
      "answer": 1
    }
  ]
}
```

- `title` (string) — quiz title
- `time_limit` (integer, optional) — time limit
- `questions` (list) — quiz questions
- Each question:

  - `question` (string) — question text
  - `options` (list) — at least 2 options
  - `answer` (integer) — index of the correct option (0-based)

## Database

- SQLite database is used by default (`database.db`).
- Tables:

  - `quiz` — quiz metadata
  - `questions` — questions for each quiz
  - `options` — multiple choice options for each question
  - `user_answers` — stores user responses

## Development

- `djlint` is used to lint and format templates.
- Bootstrap 5 is used for UI.
- Static and template files are in `static/` and `templates/` folders.
- CSRF protection enabled via Flask-WTF.

## License

MIT License
