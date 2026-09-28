# MVP implementation plan

## Goal

Turn the existing landing page and Flask scaffolding into a usable, locally runnable code-reading practice app. A student should be able to paste study material, generate a small set of questions, answer them, learn from explanations, and see a result.

Keep the first release focused on one end-to-end loop. Do not spend MVP time on payments, elaborate analytics, source libraries, or multiple AI vendors.

## Repository starting point

- The React/Vite app in `quiz_app/frontend/src/App.jsx` renders the landing page. Its login and pricing routes are placeholders; there is no working practice UI or API client.
- `quiz_app/app.py` already has Flask routes for auth, quiz text upload/paste, question/answer/results/restart, API-key settings, AI generation, and AI chat.
- `quiz_app/ai_service.py` currently emits a custom delimited text format, while `quiz_app/quiz_logic.py` parses it. The sample in `examples/sample-quiz.txt` shows the format.
- The backend expects a signed-in user and a stored OpenRouter API key for generation. There is no corresponding frontend settings flow.
- Quiz data is currently held in Flask's default client-side session cookie. The DB history functions exist, but result persistence and quiz ownership/session lifecycle should be reviewed before relying on them.

## Recommended MVP decisions

1. **One provider, one flow:** use OpenRouter for the first integration; keep credentials server-side. Prefer one server-configured `OPENROUTER_API_KEY` for a private/demo MVP so students do not need to bring their own key. If this is meant for public multi-user deployment, stop and decide on billing/abuse controls before enabling a shared paid key.
2. **Structured contract:** make JSON the canonical generation format, with a schema version and strict server validation. Keep parsing the legacy text format only if needed for existing demo/import compatibility.
3. **Low-friction access:** allow an anonymous local practice session first. Defer account signup/login and history persistence until the core loop works; if retaining auth, wire it end to end instead of exposing placeholder navigation.
4. **Small scope:** multiple-choice output/tracing questions only, one language initially (Python is a sensible default), 3–5 questions per set, easy/medium difficulty.

## Work sequence

### 1. Establish the contract and session lifecycle

- Document the API request/response shapes used by the MVP.
- Implement a versioned practice-set model matching the schema in `README.md` (source metadata, settings, questions with prompt/code/choices/internal answer/explanation).
- Ensure student-facing question responses omit answer and explanation until submission.
- Replace inconsistent session fields (`current_question` versus `current_index`, and split session state) with a clear lifecycle. For a single-process local MVP, server-side session storage or a generated session ID backed by SQLite is safer than putting all questions and answers in the cookie.
- Make answer submission idempotency/duplicate clicks predictable; define completion and restart behavior.
- Validate user input size, question counts, difficulty, language, choice count, unique choice IDs, answer membership, and nonempty explanation.

### 2. Make AI generation reliable

- Use a stable system instruction describing the learning goal: generate code-reading questions grounded only in the provided source, with one unambiguous answer and a concise step-by-step explanation.
- Request structured JSON matching the canonical contract (use provider structured output/JSON mode where available).
- Validate all generated records on the server. On invalid output, retry once with a repair instruction or return a useful error; never start a partially valid set silently.
- Preserve code formatting and language labels. Keep prompt/source size bounded and return actionable provider errors without logging secrets or full sensitive source by default.
- Put provider configuration in environment variables and document `.env.example` (with no real keys). Never expose credentials to React.

### 3. Build the student flow in React

- Keep the existing landing page, but point its primary CTA to a real practice route.
- Add a source/settings screen: textarea for notes/code, optional title/topic, language selector (initially Python), difficulty, question count, and Generate button.
- Add clear idle, generating, validation/provider error, and retry states. Disable duplicate submission while generation is running.
- Add practice screen: progress indicator, readable code block, question text, accessible answer controls, submit action, and feedback state with explanation after submission. Provide next-question navigation only after feedback.
- Add results screen with score, correct/total, review of missed questions/explanations, retry, and new-set actions.
- Make layout responsive and preserve the current design language. Ensure keyboard operation, visible focus, semantic labels, and sufficient contrast.
- Use a small API helper that consistently handles JSON, credentials if sessions are retained, and server error messages.

### 4. Choose the minimum identity and persistence story

- For an anonymous MVP, use a random server-side practice-session ID and expire old sessions; no account UI should imply saved history.
- If accounts remain in scope, complete signup/login/logout/current-user UI, secure password hashing, stable session secret, authenticated settings, and result persistence together. Do not leave dead auth links or claim progress is saved when it is not.
- Make database paths explicit and stable relative to the application/database configuration rather than the current working directory.

### 5. Clean local setup and safety gaps

- Add `.env.example` for required configuration, clarify development defaults, and confirm frontend proxy/API origin behavior.
- Set upload size limits if retaining uploads; avoid writing user filenames directly into a shared upload directory. For the simplest MVP, prioritize paste-in source and postpone file upload.
- Configure production-safe cookie flags when HTTPS is used; replace development secrets and random-per-start encryption-key fallback for any persisted encrypted values.
- Remove or defer endpoints/UI that are not part of the MVP (especially chat, provider selection, and pricing) so they do not create false expectations.

### 6. Verify the complete flow

Follow repository guidance if present. Add/adjust focused checks for schema validation, malformed AI output, answer correctness/progress/completion, and anonymous or authenticated isolation as appropriate. Then manually exercise:

1. Fresh app startup and landing-page CTA.
2. Generation success from a representative Python snippet.
3. Empty input, oversized input, provider failure, and malformed model response.
4. Correct and incorrect answers, explanation visibility, final score, retry, and new practice set.
5. Refresh/back navigation behavior during an active set.
6. `npm run build` and the relevant backend checks; fix failures introduced by the work.

## MVP acceptance criteria

- A new student can get from the landing page to practice without a broken login/settings path.
- Pasting a short Python snippet yields the requested number of valid, code-grounded questions or a clear recoverable error.
- Correct answers are not exposed before submission; after submission, the student sees correctness and a useful explanation.
- Progress, final score, retry, and starting a new set behave consistently.
- Refresh/session behavior is deliberate and does not mix one student's quiz with another's.
- AI credentials remain on the server and local setup is documented.
- The interface works at phone and desktop widths and can be used from the keyboard.

## Suggested order for the next agent

Start by inspecting the existing route and frontend behavior, then agree on the JSON contract and session model. Implement and validate the backend contract before connecting the React flow; complete one generated question set end to end before polishing secondary pages. Keep changes within this repo, report any unresolved product decision (especially shared API-key exposure for public deployment), and summarize the finished flow and verification performed.
