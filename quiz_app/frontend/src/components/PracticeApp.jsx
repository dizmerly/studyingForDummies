/*
 * The practice flow lives here: source entry, one question at a time, and
 * results. The server owns answers and progress. Local storage remembers only
 * the set ID so a refreshed page can resume the signed-in user's session.
 */
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import ThemeToggle from './ThemeToggle';

const storageKey = 'practiceSetId';

export default function PracticeApp({ theme, onToggleTheme }) {
  const [setId, setSetId] = useState(() => localStorage.getItem(storageKey));
  const [phase, setPhase] = useState('auth-loading');
  const [user, setUser] = useState(null);
  const [demoMode, setDemoMode] = useState(false);
  const [savedSets, setSavedSets] = useState([]);
  const [title, setTitle] = useState('');
  const [question, setQuestion] = useState(null);
  const [nextQuestion, setNextQuestion] = useState(null);
  const [progress, setProgress] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [results, setResults] = useState(null);
  const [choiceId, setChoiceId] = useState('');
  const [error, setError] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [sourceTitle, setSourceTitle] = useState('');
  const [difficulty, setDifficulty] = useState('easy');
  const [questionCount, setQuestionCount] = useState(3);
  const [language, setLanguage] = useState('Python');

  useEffect(() => {
    Promise.all([api.me(), api.config()]).then(([auth, config]) => {
      setUser(auth.user);
      setDemoMode(config.demoMode);
      setPhase(auth.user ? (localStorage.getItem(storageKey) ? 'loading' : 'source') : 'sign-in');
    }).catch((loadError) => { setError(loadError.message); setPhase('sign-in'); });
  }, []);

  useEffect(() => {
    if (user) api.listSets().then((data) => setSavedSets(data.sets)).catch(() => {});
  }, [user, setId]);

  useEffect(() => {
    if (!setId || !user) return;
    api.getSet(setId).then((data) => {
      setTitle(data.title);
      setQuestion(data.question);
      setNextQuestion(data.nextQuestion || null);
      setFeedback(data.feedback || null);
      setChoiceId(data.feedback?.selectedChoiceId || '');
      setProgress(data.progress);
      setPhase('question');
    }).catch((loadError) => {
      localStorage.removeItem(storageKey);
      setSetId(null);
      setError(loadError.message);
      setPhase('source');
    });
  }, [setId, user]);

  async function signInDemo() {
    try {
      const data = await api.demoLogin();
      setUser(data.user);
      setError('');
      setPhase(setId ? 'loading' : 'source');
    } catch (loginError) { setError(loginError.message); }
  }

  async function signOut() {
    await api.logout();
    localStorage.removeItem(storageKey);
    setSetId(null);
    setUser(null);
    setSavedSets([]);
    setPhase('sign-in');
  }

  async function useSample() {
    setError('');
    setPhase('generating');
    try { openSet(await api.sample()); }
    catch (sampleError) { setError(sampleError.message); setPhase('source'); }
  }

  function openSet(data) {
    localStorage.setItem(storageKey, data.id);
    setSetId(data.id);
    setTitle(data.title);
    setQuestion(data.question);
    setProgress(data.progress);
    setFeedback(data.feedback || null);
    setNextQuestion(data.nextQuestion || null);
    setChoiceId(data.feedback?.selectedChoiceId || '');
    setPhase('question');
  }

  async function generate(event) {
    event.preventDefault();
    if (!sourceText.trim()) {
      setError('Paste some code or notes first.');
      return;
    }
    if (sourceText.length > 5000) {
      setError('Keep the source under 5,000 characters.');
      return;
    }
    setError('');
    setPhase('generating');
    try {
      const data = await api.generate(
        { text: sourceText, title: sourceTitle, language: language.trim() },
        { difficulty, questionCount: Number(questionCount) },
      );
      openSet(data);
    } catch (generateError) {
      setError(generateError.message);
      setPhase('source');
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!choiceId || feedback) return;
    setError('');
    setPhase('submitting');
    try {
      const data = await api.answer(setId, question.id, choiceId);
      setFeedback(data.feedback);
      setNextQuestion(data.nextQuestion);
      setProgress(data.progress);
    } catch (answerError) {
      setError(answerError.message);
    } finally {
      setPhase('question');
    }
  }

  async function showResults() {
    setError('');
    try {
      setResults(await api.results(setId));
      setPhase('results');
    } catch (resultsError) {
      setError(resultsError.message);
    }
  }

  async function retry() {
    setError('');
    try {
      const data = await api.retry(setId);
      setQuestion(data.question);
      setProgress(data.progress);
      setNextQuestion(null);
      setFeedback(null);
      setChoiceId('');
      setResults(null);
      setPhase('question');
    } catch (retryError) {
      setError(retryError.message);
    }
  }

  function startNew() {
    localStorage.removeItem(storageKey);
    setSetId(null);
    setQuestion(null);
    setResults(null);
    setFeedback(null);
    setError('');
    setPhase('source');
  }

  return (
    <div className="practice-shell">
      <header className="practice-header page-width">
        <a className="brand" href="/" aria-label="Studying For Dummies home"><span className="brand-mark">S</span>Studying For Dummies</a>
        <div className="practice-header-actions"><a className="text-button" href="/pricing">Pricing</a><ThemeToggle theme={theme} onToggle={onToggleTheme} />
          {setId && <button className="text-button" type="button" onClick={startNew}>New set</button>}
          {user && <button className="text-button" type="button" onClick={signOut}>Sign out</button>}
        </div>
      </header>
      <main className="practice-main page-width">
        {phase === 'auth-loading' && <p role="status">Checking your sign-in…</p>}
        {phase === 'sign-in' && <section className="practice-panel"><p className="eyebrow">Your practice space</p><h1>Sign in to save your practice sets.</h1>
          <p className="form-intro">Use your Google account to keep the cards you create and return to them later.</p>
          {error && <p className="error-message" role="alert">{error}</p>}
          <a className="button button-primary" href="/api/auth/google">Continue with Google</a>
          {demoMode && <button className="button button-outline demo-button" type="button" onClick={signInDemo}>Use local demo account</button>}
        </section>}
        {phase === 'loading' && <p role="status">Loading your practice set…</p>}
        {(phase === 'source' || phase === 'generating') && (
          <section className="practice-panel" aria-labelledby="source-heading">
            <p className="eyebrow">Start a practice set</p>
            <h1 id="source-heading">What are you studying?</h1>
            <p className="form-intro">Paste a short code snippet or notes in any programming language. We’ll make a few code-reading questions from it.</p>
            {error && <p className="error-message" role="alert">{error}</p>}
            <form onSubmit={generate} className="source-form">
              <label htmlFor="source-title">Title or topic <span>(optional)</span></label>
              <input id="source-title" maxLength="120" value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} placeholder="Loops and lists" />
              <label htmlFor="source-text">Code or notes</label>
              <textarea id="source-text" required maxLength="5000" rows="11" value={sourceText} onChange={(event) => setSourceText(event.target.value)} placeholder={'const values = [1, 2, 3];\nfor (const value of values) console.log(value * 2);'} />
              <p className="field-hint">{sourceText.length.toLocaleString()} / 5,000 characters. Avoid pasting private information.</p>
              <div className="form-row">
                <div><label htmlFor="language">Language</label><input id="language" required maxLength="60" value={language} onChange={(event) => setLanguage(event.target.value)} placeholder="e.g. JavaScript, Java, C++" /></div>
                <div><label htmlFor="difficulty">Difficulty</label><select id="difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option></select></div>
                <div><label htmlFor="count">Questions</label><select id="count" value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))}><option value="3">3</option><option value="4">4</option><option value="5">5</option></select></div>
              </div>
              <button className="button button-primary" type="submit" disabled={phase === 'generating'}>{phase === 'generating' ? 'Generating questions…' : 'Generate questions'}</button>
              {demoMode && <button className="button button-outline" type="button" disabled={phase === 'generating'} onClick={useSample}>Try sample cards without AI</button>}
            </form>
            {savedSets.length > 0 && <div className="saved-sets"><h2>Your saved sets</h2><ul>{savedSets.map((item) => <li key={item.id}>
              <button type="button" onClick={() => { setSetId(item.id); setPhase('loading'); }}><strong>{item.title}</strong><span>{item.language} · {item.progress.answered}/{item.progress.total} answered</span></button>
            </li>)}</ul></div>}
          </section>
        )}
        {(phase === 'question' || phase === 'submitting') && question && (
          <section className="practice-panel" aria-labelledby="question-heading">
            <div className="question-top"><p className="eyebrow">{title}</p><p className="progress-label">Question {feedback ? progress.answered : progress.answered + 1} of {progress.total}</p></div>
            <div className="progress-track" role="progressbar" aria-label="Questions answered" aria-valuenow={progress.answered} aria-valuemin="0" aria-valuemax={progress.total}><span style={{ width: `${100 * progress.answered / progress.total}%` }} /></div>
            <h1 id="question-heading">{question.prompt}</h1>
            <pre className="code-block"><code>{question.code.text}</code></pre>
            {error && <p className="error-message" role="alert">{error}</p>}
            <form onSubmit={submitAnswer}>
              <fieldset disabled={Boolean(feedback) || phase === 'submitting'}>
                <legend>Choose one answer</legend>
                <div className="choice-list">{question.choices.map((choice) => (
                  <label key={choice.id} className={`choice ${choiceId === choice.id ? 'selected' : ''}`}>
                    <input type="radio" name="choice" value={choice.id} checked={choiceId === choice.id} onChange={() => setChoiceId(choice.id)} />
                    <span>{choice.text}</span>
                  </label>
                ))}</div>
              </fieldset>
              {!feedback && <button className="button button-primary" type="submit" disabled={!choiceId || phase === 'submitting'}>{phase === 'submitting' ? 'Checking…' : 'Check answer'}</button>}
            </form>
            {feedback && <div className={`feedback ${feedback.correct ? 'correct' : 'incorrect'}`} role="status">
              <h2>{feedback.correct ? 'That’s right.' : 'Not quite.'}</h2>
              {!feedback.correct && <p>Correct answer: {question.choices.find((choice) => choice.id === feedback.correctChoiceId)?.text}</p>}
              <p>{feedback.explanation}</p>
              {progress.completed ? <button className="button button-primary" onClick={showResults}>See results</button> : <button className="button button-primary" onClick={() => { setQuestion(nextQuestion); setFeedback(null); setChoiceId(''); }}>Next question</button>}
            </div>}
          </section>
        )}
        {phase === 'results' && results && <section className="practice-panel" aria-labelledby="results-heading">
          <p className="eyebrow">Practice complete</p><h1 id="results-heading">{results.title}</h1>
          <p className="score-line">{results.progress.score} / {results.progress.total} correct</p>
          {results.missed.length > 0 ? <div className="review"><h2>Review missed questions</h2>{results.missed.map(({ question: missed, correctChoiceId, explanation }) => <article key={missed.id}><h3>{missed.prompt}</h3><pre className="code-block"><code>{missed.code.text}</code></pre><p><strong>Answer:</strong> {missed.choices.find((choice) => choice.id === correctChoiceId)?.text}</p><p>{explanation}</p></article>)}</div> : <p>You got every question right.</p>}
          {error && <p className="error-message" role="alert">{error}</p>}
          <div className="result-actions"><button className="button button-primary" onClick={retry}>Try this set again</button><button className="button button-outline" onClick={startNew}>Start a new set</button></div>
        </section>}
      </main>
    </div>
  );
}
