"""Contract and lifecycle checks for the anonymous practice API."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quiz_app import practice
from quiz_app import app as appModule
from quiz_app import ai_service


SET = {
    'schemaVersion': 1, 'title': 'Loops',
    'questions': [{
        'id': f'q{index}', 'type': 'code_output', 'prompt': 'What prints?',
        'code': {'language': 'python', 'text': f'print({index})'},
        'choices': [{'id': choice, 'text': f'{index}-{choice}'} for choice in 'abcd'],
        'answer': {'choiceId': 'a'}, 'explanation': 'Print runs once.', 'difficulty': 'easy',
    } for index in range(3)],
}
SOURCE = {'text': 'for x in range(3): print(x)', 'title': 'Loops', 'language': 'python'}
SETTINGS = {'questionCount': 3, 'difficulty': 'easy'}


class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        practice.DATABASE_PATH = Path(self.tempDir.name) / 'practice.sqlite3'
        appModule.app.config['TESTING'] = True
        self.client = appModule.app.test_client()

    def tearDown(self):
        self.tempDir.cleanup()

    def test_validation_rejects_bad_answer(self):
        invalid = {**SET, 'questions': [dict(question) for question in SET['questions']]}
        invalid['questions'][0]['answer'] = {'choiceId': 'missing'}
        with self.assertRaises(practice.PracticeError):
            practice.validateSet(invalid, SOURCE, SETTINGS)

    def test_lifecycle_and_isolation(self):
        with patch.object(appModule, 'generateSet', return_value=practice.validateSet(SET, SOURCE, SETTINGS)):
            created = self.client.post('/api/practice-sets/generate', json={'source': SOURCE, 'settings': SETTINGS})
        self.assertEqual(created.status_code, 201)
        setId = created.json['id']
        self.assertNotIn('answer', created.json['question'])
        self.assertEqual(appModule.app.test_client().get(f'/api/practice-sets/{setId}').status_code, 404)
        self.assertEqual(self.client.get(f'/api/practice-sets/{setId}/results').status_code, 400)
        for index in range(3):
            answer = self.client.post(f'/api/practice-sets/{setId}/answers', json={
                'questionId': f'q{index}', 'choiceId': 'b' if index == 0 else 'a'})
            self.assertEqual(answer.status_code, 200)
            self.assertEqual(answer.json['feedback']['correct'], index != 0)
            duplicate = self.client.post(f'/api/practice-sets/{setId}/answers', json={
                'questionId': f'q{index}', 'choiceId': 'a'})
            self.assertEqual(duplicate.json['feedback']['selectedChoiceId'], 'b' if index == 0 else 'a')
        results = self.client.get(f'/api/practice-sets/{setId}/results')
        self.assertEqual(results.json['progress']['score'], 2)
        self.assertEqual(len(results.json['missed']), 1)
        self.assertEqual(self.client.post(f'/api/practice-sets/{setId}/retry').json['progress']['answered'], 0)

    def test_bad_request_and_provider_error(self):
        response = self.client.post('/api/practice-sets/generate', json={'source': {**SOURCE, 'text': ''}, 'settings': SETTINGS})
        self.assertEqual(response.status_code, 400)
        with patch.object(appModule, 'generateSet', side_effect=appModule.AIServiceError('Provider unavailable')):
            response = self.client.post('/api/practice-sets/generate', json={'source': SOURCE, 'settings': SETTINGS})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json['error'], 'Provider unavailable')

    def test_malformed_generation_retries_once(self):
        message = type('Message', (), {'content': '{"schemaVersion":1,"questions":[]}'})()
        response = type('Response', (), {'choices': [type('Choice', (), {'message': message})()]})()
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}), patch.object(ai_service, 'OpenAI') as client:
            client.return_value.chat.completions.create.return_value = response
            with self.assertRaises(ai_service.AIServiceError):
                ai_service.generateSet(SOURCE, SETTINGS)
            self.assertEqual(client.return_value.chat.completions.create.call_count, 2)
            request = client.return_value.chat.completions.create.call_args.kwargs
            self.assertEqual(request['model'], 'gpt-6-luna')
            self.assertEqual(request['reasoning_effort'], 'medium')
            self.assertNotIn('temperature', request)
            self.assertEqual(request['messages'][0]['role'], 'developer')


if __name__ == '__main__':
    unittest.main()
