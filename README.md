# Studying For Dummies

A small web app for turning study material into quizzes and practicing with immediate feedback. The app currently supports formatted quiz text and AI-generated multiple-choice quizzes.

## Stack

- React and Vite frontend in `quiz_app/frontend`
- Flask API in `quiz_app`
- SQLite for local account and quiz-history storage
- OpenAI API for AI quiz generation

## Run locally

Requirements: Python 3.10+ and Node.js 20+.

1. Install the Python dependencies:

   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Start the API in one terminal:

   ```sh
   cd quiz_app
   python app.py
   ```

3. Install and start the frontend in another terminal:

   ```sh
   cd quiz_app/frontend
   npm install
   npm run dev
   ```

Open the URL printed by Vite. The Vite development server forwards `/api` requests to Flask on port `5001`.

To serve the frontend from Flask, build it first:

```sh
cd quiz_app/frontend
npm run build
cd ..
python app.py
```

Open `http://localhost:5001`.

## Configuration

Set these environment variables before deployment:

- `SECRET_KEY`: a long, random Flask session secret.
- `ENCRYPTION_KEY`: a persistent Fernet key used to encrypt stored API keys. Generate one with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and keep it in the deployment provider's secret store.
- `FRONTEND_ORIGIN`: the frontend origin if it is hosted separately. The local development default is `http://localhost:5173`.
- `PORT`: optional Flask listening port; defaults to `5001`.

The AI generation screen currently requires each signed-in user to provide an API key in Settings. Never put provider API keys in frontend code.

## Quiz text format

See [`examples/sample-quiz.txt`](examples/sample-quiz.txt) for a valid example. Questions use `QUESTION`, `CHOICES`, and `ANSWER` blocks; optional `CODE` blocks can hold code snippets.
