# Studying For Dummies

A code-reading practice app. Sign in with Google, paste code or notes in any programming language, generate 3–5 questions, and review explanations. Practice sets and attempts are saved per user in SQLite.

## Run locally

Requires Python 3.10+ and Node.js 20+.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `SECRET_KEY`, `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET` in `.env`. Register `http://localhost:5173/api/auth/google/callback` as an authorized redirect URI for your Google OAuth web application. Then run:

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

Open `http://localhost:5173`. The development server forwards `/api` to Flask at `127.0.0.1:5001`.

To inspect the interface without Google credentials or OpenAI charges, set `LOCAL_DEMO_MODE=true` **only for local development**. The practice page offers a local demo account and a hand-authored Python sample set. This mode is restricted to loopback requests and does not send the sample to OpenAI.

## Configuration

- `OPENAI_API_KEY`: server-side key for generated questions.
- `OPENAI_MODEL`: defaults to `gpt-6-luna`.
- `OPENAI_REASONING_EFFORT`: defaults to `medium`.
- `SECRET_KEY`: long random secret for signed session cookies.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: OAuth credentials.
- `GOOGLE_REDIRECT_URI`: callback URL registered with Google. Defaults to the API origin plus `/api/auth/google/callback` if omitted; set it explicitly for Vite development.
- `ALLOWED_EMAILS`: optional comma-separated list of Google emails allowed into the app. If empty, any verified Google account can sign in.
- `DAILY_GENERATION_LIMIT`: maximum generated sets per user per UTC day; defaults to `10`. Failed generations do not count.
- `PRACTICE_DB_PATH`: SQLite path; defaults to `quiz_app/practice.sqlite3`.
- `FRONTEND_ORIGIN`: frontend URL for post-login redirect and CORS; defaults to `http://localhost:5173`.
- `PORT`: Flask port; defaults to `5001`.
- `COOKIE_SECURE`: set to `true` behind HTTPS.

For public use, review `ALLOWED_EMAILS`, the generation limit, and your provider's project spend cap before allowing broad access to a shared paid API key. Keep `.env` and all credentials out of the repository.

## Data and API

SQLite has a `users` table containing a stable app ID, Google subject ID, verified email, display name, and creation time. No passwords are stored. The signed HTTP-only cookie holds only the app user ID. Practice sets, answer keys, and attempts stay in SQLite and are scoped to that ID. Saved sets persist until removed from the database.

The input page accepts up to **5,000 characters** and a language name up to 60 characters. The backend enforces both limits. Generated sets contain a title, source metadata, settings, and validated questions. Student-facing responses omit correct answers and explanations until submission.

- `GET /api/auth/me`, `GET /api/auth/google`, `GET /api/auth/google/callback`, `POST /api/auth/logout`: account flow.
- `GET /api/practice-sets`: list the signed-in user's saved sets.
- `POST /api/practice-sets/generate`: generate a set from `{source: {text, title, language}, settings: {difficulty, questionCount}}`.
- `GET /api/practice-sets/<id>`: resume a set.
- `POST /api/practice-sets/<id>/answers`: submit one answer.
- `GET /api/practice-sets/<id>/results`: completed results.
- `POST /api/practice-sets/<id>/retry`: clear attempts and retry.

With `LOCAL_DEMO_MODE=true`, `POST /api/auth/demo` signs into the local demo account and `POST /api/practice-sets/sample` saves a hand-authored three-card set. These routes are unavailable outside local demo mode.

## UI

The header links to Pricing. The pricing page is a template with Free, Monthly, and Credits sections; prices and billing are not implemented. The theme follows the device's light/dark preference until the user selects a theme with the header icon. That selection is saved in local storage.
