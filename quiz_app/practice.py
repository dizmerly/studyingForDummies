"""Validate practice sets and keep each signed-in user's sets in SQLite."""
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get('PRACTICE_DB_PATH', 'practice.sqlite3'))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = APP_DIR / DATABASE_PATH


class PracticeError(ValueError):
    pass


def validateSet(data, source, settings):
    if not isinstance(data, dict) or data.get('schemaVersion') != 1:
        raise PracticeError('Generated set has an unsupported schema version.')
    if not isinstance(data.get('title'), str) or not data['title'].strip():
        raise PracticeError('Generated set needs a title.')
    questions = data.get('questions')
    if not isinstance(questions, list) or len(questions) != settings['questionCount']:
        raise PracticeError('Generated set has the wrong number of questions.')
    seenIds = set()
    for question in questions:
        if not isinstance(question, dict):
            raise PracticeError('A generated question is invalid.')
        questionId = question.get('id')
        if not isinstance(questionId, str) or not questionId.strip() or questionId in seenIds:
            raise PracticeError('Question IDs must be unique and nonempty.')
        seenIds.add(questionId)
        if question.get('type') not in ('code_output', 'code_tracing'):
            raise PracticeError('Only code output and tracing questions are supported.')
        if not isinstance(question.get('prompt'), str) or not question['prompt'].strip():
            raise PracticeError('A question prompt is missing.')
        code = question.get('code')
        if (not isinstance(code, dict) or not isinstance(code.get('language'), str)
                or code['language'].casefold() != source['language'].casefold()
                or not isinstance(code.get('text'), str) or not code['text'].strip()
                or len(code['text']) > 5000):
            raise PracticeError('Every question needs a code snippet in the selected language.')
        code['language'] = source['language']
        choices = question.get('choices')
        if not isinstance(choices, list) or len(choices) != 4:
            raise PracticeError('Every question needs four choices.')
        choiceIds = set()
        choiceTexts = set()
        for choice in choices:
            if not isinstance(choice, dict) or not isinstance(choice.get('id'), str) or not choice['id'].strip() or not isinstance(choice.get('text'), str) or not choice['text'].strip():
                raise PracticeError('A choice is missing its ID or text.')
            choiceIds.add(choice['id'])
            choiceTexts.add(choice['text'].strip())
        if len(choiceIds) != 4 or len(choiceTexts) != 4 or not isinstance(question.get('answer'), dict) or question['answer'].get('choiceId') not in choiceIds:
            raise PracticeError('Choices must have unique IDs and one valid answer.')
        if not isinstance(question.get('explanation'), str) or not question['explanation'].strip():
            raise PracticeError('Every answer needs an explanation.')
        if (question.get('difficulty') not in ('easy', 'medium', 'hard')
                or (settings['difficulty'] != 'mixed' and question['difficulty'] != settings['difficulty'])):
            raise PracticeError('Question difficulty does not match the request.')
    return {
        'schemaVersion': 1,
        'title': (data.get('title') or source['title'] or f"{source['language']} code practice")[:120],
        'source': {'title': source['title'], 'language': source['language']},
        'settings': settings,
        'questions': questions,
    }


@contextmanager
def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS practiceSets (
                id TEXT PRIMARY KEY, ownerId TEXT NOT NULL, data TEXT NOT NULL,
                attempts TEXT NOT NULL, createdAt INTEGER NOT NULL)''')
            connection.execute('''CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, googleSub TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL, name TEXT NOT NULL, createdAt INTEGER NOT NULL)''')
            connection.execute('''CREATE TABLE IF NOT EXISTS generationUsage (
                userId TEXT NOT NULL, day TEXT NOT NULL, count INTEGER NOT NULL,
                PRIMARY KEY (userId, day))''')
            yield connection
    finally:
        connection.close()


def createSet(ownerId, practiceSet):
    setId = uuid.uuid4().hex
    with connect() as connection:
        connection.execute('INSERT INTO practiceSets VALUES (?, ?, ?, ?, ?)',
                           (setId, ownerId, json.dumps(practiceSet), '{}', int(time.time())))
    return setId


def getSet(ownerId, setId):
    with connect() as connection:
        row = connection.execute('SELECT data, attempts FROM practiceSets WHERE id = ? AND ownerId = ?',
                                 (setId, ownerId)).fetchone()
    if row is None:
        raise PracticeError('Practice set not found.')
    return json.loads(row['data']), json.loads(row['attempts'])


def safeQuestion(question):
    return {key: question[key] for key in ('id', 'type', 'prompt', 'code', 'choices', 'difficulty')}


def recordAnswer(ownerId, setId, questionId, choiceId):
    # A write lock makes duplicate submissions return the original feedback.
    with connect() as connection:
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute('SELECT data, attempts FROM practiceSets WHERE id = ? AND ownerId = ?',
                                 (setId, ownerId)).fetchone()
        if row is None:
            raise PracticeError('Practice set not found.')
        practiceSet, attempts = json.loads(row['data']), json.loads(row['attempts'])
        questionIndex = next((index for index, item in enumerate(practiceSet['questions']) if item['id'] == questionId), None)
        if questionIndex is None:
            raise PracticeError('Question not found.')
        question = practiceSet['questions'][questionIndex]
        if questionId in attempts:
            return feedback(question, attempts[questionId], len(practiceSet['questions']), questionIndex)
        if questionIndex != len(attempts):
            raise PracticeError('Answer the current question first.')
        if choiceId not in {choice['id'] for choice in question['choices']}:
            raise PracticeError('Choose one of the available answers.')
        attempts[questionId] = choiceId
        connection.execute('UPDATE practiceSets SET attempts = ? WHERE id = ?', (json.dumps(attempts), setId))
    return feedback(question, choiceId, len(practiceSet['questions']), questionIndex)


def feedback(question, choiceId, total, index):
    return {'questionId': question['id'], 'selectedChoiceId': choiceId,
            'correct': choiceId == question['answer']['choiceId'],
            'correctChoiceId': question['answer']['choiceId'],
            'explanation': question['explanation'], 'completed': index + 1 == total}


def progress(practiceSet, attempts):
    questions = practiceSet['questions']
    completed = len(attempts) == len(questions)
    score = sum(attempts.get(item['id']) == item['answer']['choiceId'] for item in questions if item['id'] in attempts)
    return {'answered': len(attempts), 'total': len(questions), 'score': score, 'completed': completed}


def resetSet(ownerId, setId):
    with connect() as connection:
        cursor = connection.execute('UPDATE practiceSets SET attempts = ? WHERE id = ? AND ownerId = ?',
                                    ('{}', setId, ownerId))
        if cursor.rowcount == 0:
            raise PracticeError('Practice set not found.')


def upsertUser(googleSub, email, name):
    with connect() as connection:
        row = connection.execute('SELECT id FROM users WHERE googleSub = ?', (googleSub,)).fetchone()
        userId = row['id'] if row else uuid.uuid4().hex
        connection.execute('''INSERT INTO users (id, googleSub, email, name, createdAt)
            VALUES (?, ?, ?, ?, ?) ON CONFLICT(googleSub) DO UPDATE SET
            email = excluded.email, name = excluded.name''',
            (userId, googleSub, email, name, int(time.time())))
    return userId


def getUser(userId):
    with connect() as connection:
        row = connection.execute('SELECT id, email, name FROM users WHERE id = ?', (userId,)).fetchone()
    return dict(row) if row else None


def listSets(ownerId):
    with connect() as connection:
        rows = connection.execute('SELECT id, data, attempts, createdAt FROM practiceSets WHERE ownerId = ? ORDER BY createdAt DESC LIMIT 50',
                                  (ownerId,)).fetchall()
    return [{'id': row['id'], 'title': json.loads(row['data'])['title'],
             'language': json.loads(row['data'])['source']['language'],
             'progress': progress(json.loads(row['data']), json.loads(row['attempts'])),
             'createdAt': row['createdAt']} for row in rows]


def reserveGeneration(userId, dailyLimit):
    day = datetime.now(timezone.utc).date().isoformat()
    with connect() as connection:
        connection.execute('BEGIN IMMEDIATE')
        row = connection.execute('SELECT count FROM generationUsage WHERE userId = ? AND day = ?', (userId, day)).fetchone()
        if row and row['count'] >= dailyLimit:
            raise PracticeError(f'Daily generation limit reached ({dailyLimit}). Try again tomorrow.')
        connection.execute('''INSERT INTO generationUsage (userId, day, count) VALUES (?, ?, 1)
            ON CONFLICT(userId, day) DO UPDATE SET count = count + 1''', (userId, day))
    return day


def refundGeneration(userId, day):
    with connect() as connection:
        connection.execute('UPDATE generationUsage SET count = MAX(0, count - 1) WHERE userId = ? AND day = ?', (userId, day))
