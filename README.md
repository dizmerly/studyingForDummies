# Studying For Dummies

An AI-assisted practice tool for computer science students. The first focus is code-reading practice: students provide notes or code, the app turns that material into short questions, and students reason through what the code does.

The product is intentionally narrow. Code reading/tracing is a foundational skill for any computer science student. Reading code is a skill that 
you need at school, and future work.

Code tracing and code comprehension are the initial use case; other kinds of study practice will be added in the future. 

## Product idea

1. A student pastes notes, a code snippet, or both, and chooses a language, topic, question count, and difficulty.
2. The backend combines the source material with a stable instruction prompt and asks an AI provider to generate questions in a structured format.
3. The backend validates and normalizes the generated data before it reaches the browser.
4. The student answers questions, sees whether the answer is correct, and can read an explanation grounded in the source material.
5. The student sees a session summary and can revisit recent practice and progress.

AI output must be treated as untrusted input: require valid structured output, validate every question, reject or repair malformed output, and do not expose answer keys before the student submits an answer.

## General project schema

This is a product and data shape to guide implementation, not a frozen API contract. Update it as the MVP becomes clearer.

### Core concepts

- **User**: account identity and preferences. Accounts are optional for a local/demo flow; persistence can be added behind sign-in.
- **Study source**: user-provided notes and/or code, with optional title, language, and topic metadata.
- **Practice set**: generated, validated questions tied to a study source and generation settings.
- **Question**: prompt, optional code snippet, answer choices or answer format, correct answer, explanation, and optional source reference.
- **Practice attempt**: a student's submitted answer and feedback for one question.
- **Session result**: aggregate score and completion metadata for a practice set.

### Suggested question schema

```json
{
  "id": "q_001",
  "type": "code_output",
  "prompt": "What does this code print?",
  "code": {
    "language": "python",
    "text": "total = 1\\nfor value in range(3):\\n    total += value\\nprint(total)"
  },
  "choices": [
    { "id": "a", "text": "3" },
    { "id": "b", "text": "4" },
    { "id": "c", "text": "5" },
    { "id": "d", "text": "6" }
  ],
  "answer": { "choiceId": "b" },
  "explanation": "The loop adds 0, then 1, then 2 to the starting value 1, producing 4.",
  "difficulty": "easy",
  "topic": "loops"
}
```

The answer and explanation belong in the internal/generated representation. A practice endpoint should return only the fields needed for the current step; return correctness and the explanation after submission.

### Suggested practice-set schema

```json
{
  "title": "Python loops: code tracing",
  "source": { "title": "Week 3 notes", "language": "python" },
  "settings": { "difficulty": "easy", "questionCount": 5 },
  "questions": ["question objects"]
}
```

### Suggested API shape

Names are proposals; keep the API consistent with the final MVP flow.

- `POST /api/practice-sets/generate` — accept source material and settings; return a validated practice set or a clear actionable error.
- `GET /api/practice-sets/<id>/questions/<question-id>` — return the student-safe question fields.
- `POST /api/practice-sets/<id>/answers` — accept an answer; return correctness, explanation, and progress.
- `GET /api/practice-sets/<id>/results` — return the completed session summary.
- `GET /api/history` — list recent saved sessions for the signed-in user, if accounts are enabled for the MVP.

## MVP scope

### Must work

- A student can start without getting trapped by unfinished login or pricing screens.
- A student can paste code/notes and choose basic generation settings.
- The server generates structured code-reading questions and validates the result before starting a session.
- The student can move through questions, submit answers, see explanations, and finish the session.
- A useful end screen shows score and a way to retry or start another set.
- Loading, empty, malformed-generation, provider, and network errors have clear UI states.
- The app can run locally with documented setup and an environment-based AI configuration that never puts secrets in frontend code.

### Later

More languages and question types, file uploads, durable source libraries, richer progress analytics, sharing, payments, and multiple AI providers can follow once the core practice loop is reliable.

## Current implementation

- React 19 and Vite frontend in `quiz_app/frontend` (currently a static marketing page with placeholder login and pricing pages).
- Flask API in `quiz_app` with initial account, quiz, API-key, AI quiz-generation, and assistant-chat routes.
- SQLite storage for accounts, quiz history, and encrypted user API keys.
- AI generation currently asks for a custom text format and parses that output; the frontend is not yet wired into these routes.
- `examples/sample-quiz.txt` demonstrates the current text format, including an optional `CODE` block.

The existing code is a starting point, not a complete MVP. In particular, align the API and frontend around one schema, make quiz sessions reliable, and decide whether the MVP uses a server-managed provider key or the current per-user API-key approach.

## Stack

- React and Vite frontend in `quiz_app/frontend`
- Flask API in `quiz_app`
- SQLite for local persistence
- OpenAI integration currently present in `quiz_app/ai_service.py`

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

The current AI generation endpoint expects a signed-in user with an OpenAI API key saved in Settings. The user-facing settings flow is not yet implemented in the frontend. Never put provider API keys in frontend code.

## Existing quiz text format

See [`examples/sample-quiz.txt`](examples/sample-quiz.txt) for an example. The current parser uses `QUESTION`, `CHOICES`, and `ANSWER` blocks, with optional `CODE` blocks. This is a legacy implementation format and may be replaced by validated JSON for the MVP.
