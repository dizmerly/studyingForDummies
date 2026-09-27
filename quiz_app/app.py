"""Flask API for anonymous code-reading practice.

A signed cookie holds only an anonymous owner ID. SQLite keeps the generated set,
answer keys, and attempts; routes return answers only after submission.
"""
import os
import uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from quiz_app.ai_service import AIServiceError, generateSet
from quiz_app.practice import PracticeError, createSet, feedback, getSet, progress, recordAnswer, resetSet, safeQuestion

APP_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = APP_DIR / 'frontend' / 'dist'
app = Flask(__name__, static_folder=str(FRONTEND_DIST / 'assets'), static_url_path='/assets')
app.secret_key = os.environ.get('SECRET_KEY', 'local-development-only-secret')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == 'true',
                  MAX_CONTENT_LENGTH=16 * 1024)
CORS(app, supports_credentials=True,
     resources={r'/api/*': {'origins': os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5173')}})


def ownerId():
    if 'ownerId' not in session:
        session['ownerId'] = uuid.uuid4().hex
    return session['ownerId']


def error(message, status=400):
    return jsonify({'error': message}), status


@app.post('/api/practice-sets/generate')
def generatePracticeSet():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error('Send a JSON request.')
    source = data.get('source')
    settings = data.get('settings')
    if not isinstance(source, dict) or not isinstance(settings, dict):
        return error('Source and settings are required.')
    text = source.get('text')
    title = source.get('title', '')
    if not isinstance(text, str) or not text.strip():
        return error('Paste some Python code or notes first.')
    if len(text) > 8000:
        return error('Source is too long. Keep it under 8,000 characters.')
    if not isinstance(title, str) or len(title) > 120:
        return error('Title must be 120 characters or fewer.')
    if source.get('language') != 'python':
        return error('Only Python is supported right now.')
    count = settings.get('questionCount')
    difficulty = settings.get('difficulty')
    if type(count) is not int or count < 3 or count > 5:
        return error('Choose 3 to 5 questions.')
    if difficulty not in ('easy', 'medium'):
        return error('Choose easy or medium difficulty.')
    cleanSource = {'text': text.strip(), 'title': title.strip(), 'language': 'python'}
    cleanSettings = {'questionCount': count, 'difficulty': difficulty}
    try:
        practiceSet = generateSet(cleanSource, cleanSettings)
        setId = createSet(ownerId(), practiceSet)
    except AIServiceError as exc:
        return error(str(exc), 503)
    return jsonify({'id': setId, 'title': practiceSet['title'], 'progress': progress(practiceSet, {}),
                    'question': safeQuestion(practiceSet['questions'][0])}), 201


@app.get('/api/practice-sets/<setId>')
def getPracticeSet(setId):
    try:
        practiceSet, attempts = getSet(ownerId(), setId)
    except PracticeError as exc:
        return error(str(exc), 404)
    state = progress(practiceSet, attempts)
    index = max(0, state['answered'] - 1)
    question = practiceSet['questions'][index]
    result = {'id': setId, 'title': practiceSet['title'], 'progress': state,
              'question': safeQuestion(question)}
    if question['id'] in attempts:
        result['feedback'] = feedback(question, attempts[question['id']], state['total'], index)
        if not state['completed']:
            result['nextQuestion'] = safeQuestion(practiceSet['questions'][state['answered']])
    return jsonify(result)


@app.post('/api/practice-sets/<setId>/answers')
def submitAnswer(setId):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('questionId'), str) or not isinstance(data.get('choiceId'), str):
        return error('Question ID and choice ID are required.')
    try:
        answer = recordAnswer(ownerId(), setId, data['questionId'], data['choiceId'])
        practiceSet, attempts = getSet(ownerId(), setId)
    except PracticeError as exc:
        return error(str(exc), 400)
    state = progress(practiceSet, attempts)
    return jsonify({'feedback': answer, 'progress': state,
                    'nextQuestion': None if state['completed'] else safeQuestion(practiceSet['questions'][state['answered']])})


@app.get('/api/practice-sets/<setId>/results')
def getResults(setId):
    try:
        practiceSet, attempts = getSet(ownerId(), setId)
    except PracticeError as exc:
        return error(str(exc), 404)
    state = progress(practiceSet, attempts)
    if not state['completed']:
        return error('Finish every question before viewing results.')
    missed = []
    for question in practiceSet['questions']:
        selected = attempts[question['id']]
        if selected != question['answer']['choiceId']:
            missed.append({'question': safeQuestion(question), 'selectedChoiceId': selected,
                           'correctChoiceId': question['answer']['choiceId'], 'explanation': question['explanation']})
    return jsonify({'title': practiceSet['title'], 'progress': state, 'missed': missed})


@app.post('/api/practice-sets/<setId>/retry')
def retryPracticeSet(setId):
    try:
        resetSet(ownerId(), setId)
        practiceSet, _ = getSet(ownerId(), setId)
    except PracticeError as exc:
        return error(str(exc), 404)
    return jsonify({'id': setId, 'title': practiceSet['title'], 'progress': progress(practiceSet, {}),
                    'question': safeQuestion(practiceSet['questions'][0])})


@app.get('/')
def index():
    return send_from_directory(FRONTEND_DIST, 'index.html')


@app.get('/<path:path>')
def frontendRoute(path):
    if path.startswith('api/'):
        return error('Not found.', 404)
    requestedFile = FRONTEND_DIST / path
    if requestedFile.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, 'index.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5001)))
