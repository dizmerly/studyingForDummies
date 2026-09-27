# Studying For Dummies

A small local app for practicing Python code reading. Paste code or notes, generate 3–5 questions with OpenAI, answer them one at a time, and review your result. No account is needed. Practice sets expire after 24 hours and are not saved as history.

## Run locally

Requires Python 3.10+ and Node.js 20+. A server-managed OpenAI API key is required for generation.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` and `SECRET_KEY` in `.env`, then load it into your shell. The app does not automatically load `.env`.

```sh
set -a
. ./.env
set +a
python -m quiz_app.app
```

In another terminal:

```sh
cd quiz_app/frontend
npm install
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`. The development server forwards `/api` to Flask at `127.0.0.1:5001`. To serve the built frontend from Flask, run `npm run build` in `quiz_app/frontend` and open `http://127.0.0.1:5001`.

For a public deployment, decide on spending limits and abuse controls before using a shared paid key. Set a unique `SECRET_KEY`, use HTTPS with `COOKIE_SECURE=true`, and keep `OPENAI_API_KEY` on the server. `PRACTICE_DB_PATH` can override the default `quiz_app/practice.sqlite3`. `FRONTEND_ORIGIN` defaults to `http://localhost:5173`; `PORT` defaults to `5001`. `OPENAI_MODEL` defaults to `gpt-6-luna`, with `OPENAI_REASONING_EFFORT=medium`.

## Practice API

All routes use JSON and a signed, HTTP-only anonymous cookie. The cookie contains only an owner ID; questions, answers, and attempts stay in SQLite. The browser remembers only the set ID in local storage. A different browser session cannot read that set. Expired sets return 404.

- `POST /api/practice-sets/generate` accepts `{ "source": { "text": "...", "title": "optional", "language": "python" }, "settings": { "difficulty": "easy", "questionCount": 3 } }`. Source is limited to 8,000 characters; difficulty can be `easy` or `medium`; count must be 3–5. Returns 201 with `{ id, title, progress, question }`.
- `GET /api/practice-sets/<id>` returns `{ id, title, progress, question }`. After an answer it also returns `feedback` and `nextQuestion` so a refresh can show the explanation again.
- `POST /api/practice-sets/<id>/answers` accepts `{ "questionId": "q1", "choiceId": "a" }` and returns `{ feedback, progress, nextQuestion }`. Repeating an answer returns the original feedback without changing the score. Questions must be answered in order.
- `GET /api/practice-sets/<id>/results` returns `{ title, progress, missed }` after all questions are answered.
- `POST /api/practice-sets/<id>/retry` clears attempts for that set and returns its first question.

Generated sets use `schemaVersion: 1` and contain a title, source metadata, settings, and exactly the requested number of questions. Each question has a unique ID, `code_output` or `code_tracing` type, prompt, Python code, four unique choices, an internal answer choice ID, an explanation, and difficulty. Student-facing questions omit the answer and explanation until submission. The server rejects malformed generation and retries once.

## Checks

```sh
python -m unittest discover -s tests -v
cd quiz_app/frontend
npm run lint
npm run build
```

The former account, upload, chat, history, and pricing features are outside this MVP.
