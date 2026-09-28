"""Hand-written cards for the loopback-only demo, with no model call."""
from quiz_app.practice import validateSet


CARDS = [
    {
        'difficulty': 'easy',
        'category': 'arithmetic',
        'prompt': 'What does this code print?',
        'code': 'x = 3\nprint(x + 2 * 4)',
        'choices': ['11', '20', '14', '24'],
        'answer': 'a',
        'explanation': 'Multiplication happens first: 2 * 4 is 8. Adding x (3) gives 11.',
    },
    {
        'difficulty': 'easy',
        'category': 'loops',
        'prompt': 'What does this loop print?',
        'code': 'total = 0\nfor n in range(1, 4):\n    total += n\nprint(total)',
        'choices': ['3', '6', '7', '10'],
        'answer': 'b',
        'explanation': 'range(1, 4) gives 1, 2, and 3. Their sum is 6.',
    },
    {
        'difficulty': 'easy',
        'category': 'conditionals',
        'prompt': 'Which word is printed?',
        'code': (
            'score = 7\nif score % 2 == 0:\n    result = "even"\n'
            'else:\n    result = "odd"\nprint(result)'
        ),
        'choices': ['even', 'odd', '7', 'Nothing'],
        'answer': 'b',
        'explanation': (
            '7 has remainder 1 when divided by 2, so the else branch '
            'sets result to "odd".'
        ),
    },
    {
        'difficulty': 'medium',
        'category': 'slicing',
        'prompt': 'What list is printed?',
        'code': 'items = [10, 20, 30, 40]\nprint(items[1:3])',
        'choices': ['[10, 20, 30]', '[20, 30, 40]', '[20, 30]', '[10, 20]'],
        'answer': 'c',
        'explanation': (
            'A slice includes index 1 (20) and stops before index 3, '
            'so it contains 20 and 30.'
        ),
    },
    {
        'difficulty': 'medium',
        'category': 'references',
        'prompt': 'What does the final line print?',
        'code': 'a = [1, 2]\nb = a\nb.append(3)\nprint(a)',
        'choices': ['[1, 2]', '[1, 2, 3]', '[3]', 'An error'],
        'answer': 'b',
        'explanation': (
            'b and a refer to the same list. Appending through b also '
            'changes the list seen through a.'
        ),
    },
    {
        'difficulty': 'medium',
        'category': 'scope',
        'prompt': 'What two numbers are printed?',
        'code': 'x = 5\ndef change(x):\n    x += 2\n    return x\nprint(change(x), x)',
        'choices': ['7 7', '5 7', '7 5', '5 5'],
        'answer': 'c',
        'explanation': 'The function changes its local x from 5 to 7. The outer x is still 5.',
    },
    {
        'difficulty': 'medium',
        'category': 'dictionaries',
        'prompt': 'What does this code print?',
        'code': (
            'counts = {}\nfor letter in "aba":\n'
            '    counts[letter] = counts.get(letter, 0) + 1\n'
            'print(counts["a"], counts["b"])'
        ),
        'choices': ['1 2', '2 1', '2 2', '1 1'],
        'answer': 'b',
        'explanation': 'The loop sees a twice and b once, so their counts are 2 and 1.',
    },
    {
        'difficulty': 'hard',
        'category': 'mutable defaults',
        'prompt': 'What does this code print across both calls?',
        'code': (
            'def add(item, bucket=[]):\n    bucket.append(item)\n'
            '    return len(bucket)\nprint(add("a"), add("b"))'
        ),
        'choices': ['1 1', '1 2', '2 2', '2 1'],
        'answer': 'b',
        'explanation': (
            'The default list is created once and reused. The first call '
            'leaves one item; the second appends another.'
        ),
    },
    {
        'difficulty': 'hard',
        'category': 'closures',
        'prompt': 'What list do these functions produce?',
        'code': (
            'funcs = []\nfor n in range(3):\n'
            '    funcs.append(lambda: n)\nprint([fn() for fn in funcs])'
        ),
        'choices': ['[0, 1, 2]', '[0, 0, 0]', '[2, 2, 2]', '[3, 3, 3]'],
        'answer': 'c',
        'explanation': (
            'Each lambda reads n when called, after the loop ends. '
            'At that point n is 2 for all three.'
        ),
    },
    {
        'difficulty': 'hard',
        'category': 'indexing',
        'prompt': 'What list remains after the loop?',
        'code': (
            'values = [1, 2, 3]\nfor index in range(len(values)):\n'
            '    values[index] += values[index - 1]\nprint(values)'
        ),
        'choices': ['[4, 6, 9]', '[1, 3, 6]', '[4, 3, 5]', '[1, 2, 3]'],
        'answer': 'a',
        'explanation': (
            'At index 0, values[-1] is 3, making 4. Index 1 adds that '
            'new 4 to 2, making 6. Index 2 adds 6 to 3, making 9.'
        ),
    },
]


def buildDemoSet():
    source = {
        'text': '\n\n'.join(card['code'] for card in CARDS),
        'title': 'Python code reading demo',
        'language': 'Python',
    }
    settings = {'questionCount': len(CARDS), 'difficulty': 'mixed'}
    raw = {
        'schemaVersion': 1,
        'title': '10 Python code-reading cards',
        'questions': [
            {
                'id': f'q{index}',
                'type': 'code_output',
                'prompt': card['prompt'],
                'code': {'language': 'Python', 'text': card['code']},
                'choices': [
                    {'id': letter, 'text': choice}
                    for letter, choice in zip('abcd', card['choices'])
                ],
                'answer': {'choiceId': card['answer']},
                'explanation': card['explanation'],
                'difficulty': card['difficulty'],
                'category': card['category'],
            }
            for index, card in enumerate(CARDS, 1)
        ],
    }
    return validateSet(raw, source, settings)
