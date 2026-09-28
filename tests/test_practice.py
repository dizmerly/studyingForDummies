"""Contract, identity, quota, and lifecycle checks for the practice API."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quiz_app import ai_service
from quiz_app import app as appModule
from quiz_app import practice


SET = {
    'schemaVersion': 1,
    'title': 'Loops',
    'questions': [
        {
            'id': f'q{index}',
            'type': 'code_output',
            'prompt': 'What prints?',
            'code': {'language': 'python', 'text': f'print({index})'},
            'choices': [
                {'id': choice, 'text': f'{index}-{choice}'}
                for choice in 'abcd'
            ],
            'answer': {'choiceId': 'a'},
            'explanation': 'Print runs once.',
            'difficulty': 'easy',
            'category': 'loops',
        }
        for index in range(3)
    ],
}
SOURCE = {
    'text': 'for x in range(3): print(x)',
    'title': 'Loops',
    'language': 'python',
}
SETTINGS = {'questionCount': 3, 'difficulty': 'easy'}


class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        practice.DATABASE_PATH = Path(self.tempDir.name) / 'practice.sqlite3'
        appModule.app.config['TESTING'] = True
        self.client = appModule.app.test_client()
        self.userId = practice.upsertUser(
            'google-test-user', 'student@example.com', 'Student'
        )
        with self.client.session_transaction() as session:
            session['userId'] = self.userId

    def tearDown(self):
        self.tempDir.cleanup()

    def generateSet(self, source=SOURCE, data=SET):
        validated = practice.validateSet(data, source, SETTINGS)
        with patch.object(appModule, 'generateSet', return_value=validated):
            return self.client.post(
                '/api/practice-sets/generate',
                json={'source': source, 'settings': SETTINGS},
            )

    def answer(self, setId, questionId, choiceId):
        return self.client.post(
            f'/api/practice-sets/{setId}/answers',
            json={
                'questionId': questionId,
                'choiceId': choiceId,
                'questionType': 'code_output',
                'category': 'loops',
            },
        )

    def test_validation_rejects_bad_answer_and_category(self):
        invalid = {**SET, 'questions': [dict(question) for question in SET['questions']]}
        invalid['questions'][0]['answer'] = {'choiceId': 'missing'}
        with self.assertRaises(practice.PracticeError):
            practice.validateSet(invalid, SOURCE, SETTINGS)

        invalid['questions'][0]['answer'] = {'choiceId': 'a'}
        invalid['questions'][0]['category'] = ''
        with self.assertRaises(practice.PracticeError):
            practice.validateSet(invalid, SOURCE, SETTINGS)

    def test_lifecycle_mistakes_and_isolation(self):
        created = self.generateSet()
        self.assertEqual(created.status_code, 201)
        setId = created.json['id']
        self.assertNotIn('answer', created.json['question'])
        self.assertEqual(created.json['question']['category'], 'loops')

        anonymous = appModule.app.test_client()
        self.assertEqual(anonymous.get(f'/api/practice-sets/{setId}').status_code, 401)
        self.assertEqual(anonymous.get('/api/question-mistakes').status_code, 401)
        self.assertEqual(self.client.get(f'/api/practice-sets/{setId}/results').status_code, 400)

        for index in range(3):
            choiceId = 'b' if index == 0 else 'a'
            answer = self.answer(setId, f'q{index}', choiceId)
            self.assertEqual(answer.status_code, 200)
            self.assertEqual(answer.json['feedback']['correct'], index != 0)

            duplicate = self.answer(setId, f'q{index}', 'a')
            self.assertEqual(duplicate.json['feedback']['selectedChoiceId'], choiceId)

        results = self.client.get(f'/api/practice-sets/{setId}/results')
        self.assertEqual(results.json['progress']['score'], 2)
        self.assertEqual(len(results.json['missed']), 1)
        self.assertEqual(results.json['missed'][0]['question']['category'], 'loops')

        mistakes = self.client.get('/api/question-mistakes').json['mistakes']
        self.assertEqual(len(mistakes), 1)
        self.assertEqual(mistakes[0]['category'], 'loops')
        self.assertEqual(mistakes[0]['questionType'], 'code_output')
        self.assertEqual(mistakes[0]['count'], 1)

        retry = self.client.post(f'/api/practice-sets/{setId}/retry')
        self.assertEqual(retry.json['progress']['answered'], 0)
        self.assertEqual(self.client.get('/api/practice-sets').json['sets'][0]['id'], setId)

    def test_answer_metadata_is_checked(self):
        setId = self.generateSet().json['id']
        mismatched = self.client.post(
            f'/api/practice-sets/{setId}/answers',
            json={
                'questionId': 'q0',
                'choiceId': 'b',
                'questionType': 'code_tracing',
                'category': 'loops',
            },
        )
        self.assertEqual(mismatched.status_code, 400)
        self.assertEqual(self.client.get('/api/question-mistakes').json['mistakes'], [])

    def test_demo_sample_set_has_categories(self):
        with patch.dict('os.environ', {'LOCAL_DEMO_MODE': 'true'}):
            response = self.client.post('/api/practice-sets/sample')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['progress']['total'], 10)
        self.assertEqual(response.json['question']['category'], 'arithmetic')

    def test_bad_request_and_provider_error(self):
        response = self.client.post(
            '/api/practice-sets/generate',
            json={'source': {**SOURCE, 'text': ''}, 'settings': SETTINGS},
        )
        self.assertEqual(response.status_code, 400)

        with patch.object(
            appModule, 'generateSet', side_effect=appModule.AIServiceError('Provider unavailable')
        ):
            response = self.client.post(
                '/api/practice-sets/generate',
                json={'source': SOURCE, 'settings': SETTINGS},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error'], 'Provider unavailable')

    def test_malformed_generation_retries_once(self):
        response = type('Response', (), {
            'status_code': 200,
            'json': lambda self: {
                'choices': [{'message': {'content': '{"schemaVersion":1,"questions":[]}'}}],
            },
        })()
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            with patch.object(ai_service.requests, 'post', return_value=response) as post:
                with self.assertRaises(ai_service.AIServiceError):
                    ai_service.generateSet(SOURCE, SETTINGS)

        self.assertEqual(post.call_count, 2)
        request = post.call_args.kwargs['json']
        self.assertEqual(request['model'], 'google/gemini-2.5-flash')
        self.assertEqual(request['response_format'], {'type': 'json_object'})
        self.assertIn('code-reading', request['messages'][0]['content'])

    def test_any_language_and_source_limit(self):
        source = {
            'text': 'console.log(1 + 2)',
            'title': 'JavaScript',
            'language': 'JavaScript',
        }
        sample = {
            **SET,
            'questions': [
                {**item, 'code': {'language': 'JavaScript', 'text': source['text']}}
                for item in SET['questions']
            ],
        }
        response = self.generateSet(source, sample)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['question']['code']['language'], 'JavaScript')

        source['text'] = 'x' * 5001
        response = self.client.post(
            '/api/practice-sets/generate',
            json={'source': source, 'settings': SETTINGS},
        )
        self.assertEqual(response.status_code, 400)

    def test_daily_generation_limit(self):
        validated = practice.validateSet(SET, SOURCE, SETTINGS)
        with patch.dict('os.environ', {'DAILY_GENERATION_LIMIT': '1'}):
            with patch.object(appModule, 'generateSet', return_value=validated):
                first = self.client.post(
                    '/api/practice-sets/generate',
                    json={'source': SOURCE, 'settings': SETTINGS},
                )
                second = self.client.post(
                    '/api/practice-sets/generate',
                    json={'source': SOURCE, 'settings': SETTINGS},
                )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 429)

    def test_google_callback_creates_stable_user_and_respects_allowlist(self):
        with self.client.session_transaction() as session:
            session.clear()

        identity = {
            'sub': 'google-new-user',
            'email': 'new@example.com',
            'email_verified': True,
            'name': 'New Student',
        }
        with patch.object(
            appModule.oauth.google,
            'authorize_access_token',
            return_value={'userinfo': identity},
        ):
            with patch.dict('os.environ', {'ALLOWED_EMAILS': 'new@example.com'}):
                response = self.client.get('/api/auth/google/callback')

        self.assertEqual(response.status_code, 302)
        user = self.client.get('/api/auth/me').json['user']
        self.assertEqual(user['email'], 'new@example.com')
        self.assertEqual(
            user['id'],
            practice.upsertUser(identity['sub'], identity['email'], identity['name']),
        )

        self.client.post('/api/auth/logout')
        self.assertIsNone(self.client.get('/api/auth/me').json['user'])

        with patch.object(
            appModule.oauth.google,
            'authorize_access_token',
            return_value={'userinfo': identity},
        ):
            with patch.dict('os.environ', {'ALLOWED_EMAILS': 'someone-else@example.com'}):
                response = self.client.get('/api/auth/google/callback')
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()
