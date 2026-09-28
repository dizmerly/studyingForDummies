"""Generate one structured code-reading set with OpenRouter.

The model sees only bounded study material. Validation is performed by practice.py;
this module retries one malformed response and returns user-safe provider errors.
"""
import json
import os
import requests
from quiz_app.practice import PracticeError, validateSet


class AIServiceError(Exception):
    pass


SYSTEM_INSTRUCTION = '''Create code-reading practice grounded only in the supplied source.
Return one JSON object with schemaVersion 1, title, and questions. Each question has:
id, type (code_output or code_tracing), prompt, code {language: the source language, text},
choices (exactly four objects with unique id and text), answer {choiceId},
explanation (concise step-by-step reasoning), difficulty (requested difficulty).
For hard questions, require careful tracing across multiple steps or subtle state changes,
while keeping the answer unambiguous and grounded in the source.
Use one unambiguous correct answer. Preserve code whitespace and the supplied language. Do not invent
unrelated code or material. Return exactly the requested number of questions.'''


def generateSet(source, settings):
    apiKey = os.environ.get('OPENROUTER_API_KEY')
    if not apiKey:
        raise AIServiceError('The server has no OpenRouter API key. Set OPENROUTER_API_KEY and restart it.')
    prompt = json.dumps({'source': source, 'settings': settings})
    for attempt in range(2):
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {apiKey}', 'Content-Type': 'application/json'},
                json={
                    'model': os.environ.get('OPENROUTER_MODEL', 'google/gemini-2.5-flash'),
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_INSTRUCTION},
                        {'role': 'user', 'content': prompt + ('\nPrevious output was invalid. Repair the JSON and follow every requirement.' if attempt else '')},
                    ],
                    'response_format': {'type': 'json_object'},
                    'max_tokens': 6000,
                },
                timeout=60,
            )
            if response.status_code == 401:
                raise AIServiceError('The server OpenRouter API key was rejected.')
            if response.status_code == 402:
                raise AIServiceError('OpenRouter has insufficient credits. Add credits and try again.')
            if response.status_code == 429:
                raise AIServiceError('OpenRouter is temporarily rate limited. Try again later.')
            if response.status_code >= 400:
                raise AIServiceError('OpenRouter rejected the generation request. Check the configured model and try again.')
            data = json.loads(response.json()['choices'][0]['message']['content'] or '')
            return validateSet(data, source, settings)
        except (ValueError, KeyError, IndexError, TypeError, PracticeError):
            if attempt:
                raise AIServiceError('Generated questions were invalid twice. Please revise your source and try again.') from None
        except requests.RequestException:
            raise AIServiceError('OpenRouter is unavailable. Try again later.') from None
    raise AIServiceError('Could not generate questions.')
