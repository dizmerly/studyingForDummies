from decimal import InvalidContext
import re


# Question regex grabber, make sure that the regex is greedy enough
# but not too greedy because otherwise following questions get swallowed 
BLOCK_RE = re.compile(
    r'"""QUESTION"""\s*(.*?)\s*'
    r'"""CHOICES"""\s*(.*?)\s*'
    r'"""ANSWER"""\s*([A-D][^\n]*)',      # <- entire answer line
    re.DOTALL | re.I
)

def parse_choices(choices_text: str):
    """Return list [('A', text), ...]  (upper-case letters)."""
    return [(m.group(1).upper(), m.group(2).strip())
            for m in re.finditer(r'([A-D]):\s*(.+)', choices_text, re.I)]

# FIXME add shuffle function in order to shuffle questions on subsequent attempts 
# or on any attempt
def shuffle_questions(questions):
    return 
    
def valid_block(question: str, choices: list[tuple[str, str]], answer_letter: str):
    """Return (True, '') or (False, reason)."""
    if not question:
        return False, "missing question text"
    if len(choices) < 2:
        return False, "fewer than two choices"
    present = {letter for letter, _ in choices}
    if answer_letter not in present:
        return False, f"answer '{answer_letter}' is not one of the choices"
    return True, ""



# ---------- driver ----------
def load_questions(file_path: str):
    """
    Load and parse questions from a file.
    
    Args:
        file_path: Path to the quiz file
    
    Returns:
        List of question dictionaries with keys: 'question', 'choices', 'answer'
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If no valid questions found
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    
    matches = BLOCK_RE.findall(content)
    
    if not matches:
        raise ValueError("No questions found in file")
    
    questions = []
    
    for i, match in enumerate(matches, start=1):
        question_text = match[0].strip()
        choices_text = match[1]
        answer_line = match[2].strip()
        
        # Parse choices
        choices = parse_choices(choices_text)
        
        # Extract answer letter
        answer_m = re.search(r'\b([A-D])\b', answer_line, re.I)
        if not answer_m:
            print(f"Warning: Question {i} skipped - no answer letter found")
            continue
        
        correct_letter = answer_m.group(1).upper()
        
        # Validate block
        ok, reason = valid_block(question_text, choices, correct_letter)
        
        if ok:
            questions.append({
                'question': question_text,
                'choices': choices,
                'answer': correct_letter
            })
        else:
            print(f"Warning: Question {i} skipped - {reason}")
    
    if not questions:
        raise ValueError("No valid questions found in file")
    
    return questions

def load_questions_from_text(text):
    """
    Parse quiz questions directly from pasted text.
    Returns list of question dicts (same as load_questions).
    """
    from io import StringIO
    f = StringIO(text)
    content = f.read()
    
    # reuse the same parsing logic as load_questions
    matches = BLOCK_RE.findall(content)
    questions = []
    for i, match in enumerate(matches, start=1):
        question_text = match[0].strip()
        choices_text = match[1]
        answer_line = match[2].strip()
        
        choices = parse_choices(choices_text)
        answer_m = re.search(r'\b([A-D])\b', answer_line, re.I)
        if not answer_m:
            continue
        correct_letter = answer_m.group(1).upper()
        
        ok, reason = valid_block(question_text, choices, correct_letter)
        if ok:
            questions.append({
                'question': question_text,
                'choices': choices,
                'answer': correct_letter
            })
    return questions

# ---------- Console Quiz Runner (Optional) ----------
def run_console_quiz(file_path: str):
    """
    Run an interactive console-based quiz.
    This is separate from load_questions so the GUI can use load_questions alone.
    """
    questions = load_questions(file_path)
    score = 0
    
    print(f"\n{'='*50}")
    print(f"Quiz loaded with {len(questions)} questions")
    print(f"{'='*50}\n")
    
    for i, q in enumerate(questions, start=1):
        print(f"\nQuestion {i}: {q['question']}")
        for letter, text in q['choices']:
            print(f"{letter}: {text}")
        
        while True:
            user_ans = input("Your answer (A/B/C/D or Q to quit): ").strip().upper()
            if user_ans in {'A', 'B', 'C', 'D', 'Q'}:
                break
            print("Invalid choice. Please enter A, B, C, D, or Q.")
        
        if user_ans == 'Q':
            print("\nQuiz aborted.")
            break
        
        if user_ans == q['answer']:
            print("✓ Correct!")
            score += 1
        else:
            print(f"✗ Incorrect. Correct answer: {q['answer']}")
    
    print(f"\n{'='*50}")
    print(f"Final Score: {score}/{i}")
    print(f"{'='*50}\n")

# ---------- For testing this module directly ----------
if __name__ == "__main__":
    import sys
    
    print("Quiz Logic Module")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # If a file is provided as argument, run console quiz
        try:
            run_console_quiz(sys.argv[1])
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("\nUsage:")
        print("  python quiz_logic.py <quiz_file.txt>  - Run console quiz")
        print("\nOr import in your GUI:")
        print("  from quiz_logic import load_questions")
        print("\nFunctions available:")
        print("  - parse_choices(text)")
        print("  - valid_block(question, choices, answer)")
        print("  - load_questions(file_path) -> returns list of question dicts")
        print("  - run_console_quiz(file_path) -> runs interactive console quiz")

