"""Generate one structured Python code-reading set with OpenAI.

The model sees only bounded study material. Validation is performed by practice.py;
this module retries one malformed response and returns user-safe provider errors.
"""
import json
import os
from openai import OpenAI, AuthenticationError, RateLimitError, APIError
from quiz_app.practice import PracticeError, validateSet


class AIServiceError(Exception):
    pass


SYSTEM_INSTRUCTION = '''Create Python code-reading practice grounded only in the supplied source.
Return one JSON object with schemaVersion 1, title, and questions. Each question has:
id, type (code_output or code_tracing), prompt, code {language: python, text},
choices (exactly four objects with unique id and text), answer {choiceId},
explanation (concise step-by-step reasoning), difficulty (requested difficulty).
Use one unambiguous correct answer. Preserve code whitespace. Do not invent
unrelated code or material. Return exactly the requested number of questions.'''


def generateSet(source, settings):
    apiKey = os.environ.get('OPENAI_API_KEY')
    if not apiKey:
        raise AIServiceError('The server has no OpenAI API key. Set OPENAI_API_KEY and restart it.')
    client = OpenAI(api_key=apiKey, timeout=30)
    prompt = json.dumps({'source': source, 'settings': settings})
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
                response_format={'type': 'json_object'},
                messages=[{'role': 'system', 'content': SYSTEM_INSTRUCTION},
                          {'role': 'user', 'content': prompt + ('\nPrevious output was invalid. Repair the JSON and follow every requirement.' if attempt else '')}],
                temperature=0.3,
            )
            data = json.loads(response.choices[0].message.content or '')
            return validateSet(data, source, settings)
        except (ValueError, KeyError, IndexError, TypeError, PracticeError):
            if attempt:
                raise AIServiceError('Generated questions were invalid twice. Please revise your source and try again.') from None
        except AuthenticationError:
            raise AIServiceError('The server OpenAI API key was rejected.') from None
        except RateLimitError:
            raise AIServiceError('OpenAI is temporarily rate limited. Try again later.') from None
        except APIError:
            raise AIServiceError('OpenAI is unavailable. Try again later.') from None
    raise AIServiceError('Could not generate questions.')
