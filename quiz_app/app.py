"""Flask API for signed-in code-reading practice."""
import os
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, jsonify, request, send_from_directory, session, redirect
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from quiz_app.ai_service import AIServiceError, generateSet
from quiz_app.practice import PracticeError, createSet, feedback, getSet, getUser, listQuestionMistakes, listSets, progress, recordAnswer, refundGeneration, reserveGeneration, resetSet, safeQuestion, upsertUser, validateSet

APP_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = APP_DIR / 'frontend' / 'dist'
app = Flask(__name__, static_folder=str(FRONTEND_DIST / 'assets'), static_url_path='/assets')
app.secret_key = os.environ.get('SECRET_KEY') or 'local-development-only-secret'
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE') == 'true',
                  MAX_CONTENT_LENGTH=32 * 1024)
CORS(app, supports_credentials=True,
     resources={r'/api/*': {'origins': os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5173')}})


oauth = OAuth(app)
oauth.register(name='google', client_id=os.environ.get('GOOGLE_CLIENT_ID'),
               client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
               server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
               client_kwargs={'scope': 'openid email profile'})


def currentUser():
    userId = session.get('userId')
    return getUser(userId) if userId else None


def ownerId():
    user = currentUser()
    return f"user:{user['id']}" if user else None


def demoEnabled():
    frontendHost = urlparse(os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5173')).hostname
    return (os.environ.get('LOCAL_DEMO_MODE') == 'true'
            and frontendHost in ('localhost', '127.0.0.1')
            and request.remote_addr in ('127.0.0.1', '::1'))


def error(message, status=400):
    return jsonify({'error': message}), status


@app.errorhandler(413)
def requestTooLarge(_error):
    return error('Request is too large. Keep source under 5,000 characters.', 413)


@app.get('/api/config')
def getConfig():
    return jsonify({'demoMode': demoEnabled()})


@app.get('/api/auth/me')
def authMe():
    return jsonify({'user': currentUser()})


@app.get('/api/auth/google')
def googleLogin():
    if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
        return error('Google sign-in is not configured on this server.', 503)
    callback = os.environ.get('GOOGLE_REDIRECT_URI') or request.url_root.rstrip('/') + '/api/auth/google/callback'
    return oauth.google.authorize_redirect(callback)


@app.get('/api/auth/google/callback')
def googleCallback():
    try:
        token = oauth.google.authorize_access_token()
        identity = token.get('userinfo') or oauth.google.parse_id_token(token)
        if not identity.get('sub') or not identity.get('email') or not identity.get('email_verified'):
            return error('Google did not provide a verified email.', 403)
        email = identity['email'].lower()
        allowed = {item.strip().lower() for item in os.environ.get('ALLOWED_EMAILS', '').split(',') if item.strip()}
        if allowed and email not in allowed:
            return error('This Google account is not allowed to use this app.', 403)
        userId = upsertUser(identity['sub'], email, identity.get('name') or email)
        session.clear()
        session['userId'] = userId
        return redirect(os.environ.get('FRONTEND_ORIGIN', 'http://localhost:5173') + '/practice')
    except Exception:
        return error('Google sign-in failed. Please try again.', 400)


@app.post('/api/auth/logout')
def logout():
    session.clear()
    return jsonify({'success': True})


@app.post('/api/auth/demo')
def demoLogin():
    if not demoEnabled():
        return error('Local demo is unavailable.', 404)
    session.clear()
    session['userId'] = upsertUser('local-demo-user', 'demo@localhost', 'Local demo')
    return jsonify({'user': currentUser()})


@app.post('/api/practice-sets/sample')
def createSample():
    if not demoEnabled() or not currentUser():
        return error('Local demo is unavailable.', 404)
    source = {'text': 'values = [2, 4]\ntotal = 0\nfor value in values:\n    total += value\nprint(total)',
              'title': 'Tracing a loop', 'language': 'python'}
    settings = {'questionCount': 3, 'difficulty': 'easy'}
    questionData = [
        ('What does this code print?', ['2', '4', '6', '8'], 'c', 'The loop adds 2 and then 4 to zero, so print shows 6.', 'loops'),
        ('How many times does the loop body run?', ['1', '2', '3', '4'], 'b', 'The list has two values, so the loop body runs once for each value.', 'loops'),
        ('What is total after the first loop iteration?', ['0', '2', '4', '6'], 'b', 'The first value is 2, and total starts at 0, so total becomes 2.', 'state-tracing'),
    ]
    raw = {'schemaVersion': 1, 'title': 'Tracing a loop', 'questions': [
        {'id': f'q{index}', 'type': 'code_tracing', 'prompt': prompt,
         'code': {'language': 'python', 'text': source['text']},
         'choices': [{'id': letter, 'text': choice} for letter, choice in zip('abcd', choices)],
         'answer': {'choiceId': answer}, 'explanation': explanation, 'difficulty': 'easy',
         'category': category}
        for index, (prompt, choices, answer, explanation, category) in enumerate(questionData, 1)]}
    practiceSet = validateSet(raw, source, settings)
    setId = createSet(ownerId(), practiceSet)
    return jsonify({'id': setId, 'title': practiceSet['title'], 'progress': progress(practiceSet, {}),
                    'question': safeQuestion(practiceSet['questions'][0])}), 201


@app.get('/api/practice-sets')
def getPracticeSets():
    owner = ownerId()
    if not owner:
        return error('Sign in to view your practice sets.', 401)
    return jsonify({'sets': listSets(owner)})


@app.post('/api/practice-sets/generate')
def generatePracticeSet():
    owner = ownerId()
    if not owner:
        return error('Sign in to generate questions.', 401)
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
        return error('Paste some code or notes first.')
    if len(text) > 5000:
        return error('Source is too long. Keep it under 5,000 characters.')
    if not isinstance(title, str) or len(title) > 120:
        return error('Title must be 120 characters or fewer.')
    language = source.get('language')
    if not isinstance(language, str) or not language.strip() or len(language.strip()) > 60:
        return error('Enter a language name (60 characters or fewer).')
    count = settings.get('questionCount')
    difficulty = settings.get('difficulty')
    if type(count) is not int or count < 3 or count > 5:
        return error('Choose 3 to 5 questions.')
    if difficulty not in ('easy', 'medium', 'hard'):
        return error('Choose easy, medium, or hard difficulty.')
    cleanSource = {'text': text.strip(), 'title': title.strip(), 'language': language.strip()}
    cleanSettings = {'questionCount': count, 'difficulty': difficulty}
    try:
        day = reserveGeneration(currentUser()['id'], max(1, int(os.environ.get('DAILY_GENERATION_LIMIT', '10'))))
    except PracticeError as exc:
        return error(str(exc), 429)
    try:
        practiceSet = generateSet(cleanSource, cleanSettings)
        setId = createSet(owner, practiceSet)
    except AIServiceError as exc:
        refundGeneration(currentUser()['id'], day)
        return error(str(exc), 503)
    except Exception:
        refundGeneration(currentUser()['id'], day)
        raise
    return jsonify({'id': setId, 'title': practiceSet['title'], 'progress': progress(practiceSet, {}),
                    'question': safeQuestion(practiceSet['questions'][0])}), 201


@app.get('/api/practice-sets/<setId>')
def getPracticeSet(setId):
    if not ownerId():
        return error('Sign in to view your practice set.', 401)
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
    if not ownerId():
        return error('Sign in to answer questions.', 401)
    data = request.get_json(silent=True)
    if (not isinstance(data, dict) or not isinstance(data.get('questionId'), str)
            or not isinstance(data.get('choiceId'), str)
            or not isinstance(data.get('questionType'), str)
            or not isinstance(data.get('category'), str)):
        return error('Question ID, choice ID, type, and category are required.')
    try:
        user = currentUser()
        answer = recordAnswer(user['id'], ownerId(), setId, data['questionId'], data['choiceId'],
                              data['questionType'], data['category'])
        practiceSet, attempts = getSet(ownerId(), setId)
    except PracticeError as exc:
        return error(str(exc), 400)
    state = progress(practiceSet, attempts)
    return jsonify({'feedback': answer, 'progress': state,
                    'nextQuestion': None if state['completed'] else safeQuestion(practiceSet['questions'][state['answered']])})


@app.get('/api/question-mistakes')
def getQuestionMistakes():
    user = currentUser()
    if not user:
        return error('Sign in to view question history.', 401)
    return jsonify({'mistakes': listQuestionMistakes(user['id'])})


@app.get('/api/practice-sets/<setId>/results')
def getResults(setId):
    if not ownerId():
        return error('Sign in to view results.', 401)
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
    if not ownerId():
        return error('Sign in to retry this set.', 401)
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
