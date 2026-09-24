import re
import logging
from typing import List, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class QuizError(Exception):
    """Custom exception for quiz-related errors."""
    pass

# Regex patterns
# The negative lookahead ensures we don't match across question boundaries
BLOCK_RE = re.compile(
    r'"""QUESTION"""\s*'
    r'((?:(?!"""QUESTION"""|"""CHOICES""").)*?)'  # Question text - stop at next block marker
    r'"""CHOICES"""\s*'
    r'((?:(?!"""QUESTION"""|"""ANSWER""").)*?)'  # Choices text - stop at next block marker
    r'"""ANSWER"""\s*'
    r'([A-D][^\n]*)',  # Answer line
    re.DOTALL | re.IGNORECASE
)

CHOICE_RE = re.compile(r'([A-D]):\s*(.+)', re.IGNORECASE)
ANSWER_LETTER_RE = re.compile(r'\b([A-D])\b', re.IGNORECASE)

def parse_choices(choices_text: str) -> List[Tuple[str, str]]:
    """
    Parse choices text into a list of tuples (letter, text).
    
    Args:
        choices_text: The raw text containing choices (e.g., "A: Choice 1\nB: Choice 2")
        
    Returns:
        List of tuples like [('A', 'Choice 1'), ('B', 'Choice 2')]
    """
    return [(m.group(1).upper(), m.group(2).strip())
            for m in CHOICE_RE.finditer(choices_text)]

def validate_block(question: str, choices: List[Tuple[str, str]], answer_letter: str) -> Tuple[bool, str]:
    """
    Validate a single question block.
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not question or not question.strip():
        return False, "Missing question text"
    if len(choices) < 2:
        return False, f"Fewer than two choices found (found {len(choices)})"
    
    # Check for empty choice text
    for letter, text in choices:
        if not text or not text.strip():
            return False, f"Choice {letter} has no text"
    
    present_letters = {letter for letter, _ in choices}
    if answer_letter not in present_letters:
        return False, f"Answer '{answer_letter}' is not among the parsed choices ({', '.join(sorted(present_letters))})"
        
    return True, ""

def parse_quiz_content(content: str) -> List[Dict[str, Any]]:
    """
    Core logic to parse quiz content string into a list of question dictionaries.
    
    Args:
        content: The full text content of the quiz file/input.
        
    Returns:
        List of question dictionaries.
        
    Raises:
        QuizError: If no valid questions are found.
    """
    matches = BLOCK_RE.findall(content)
    
    if not matches:
        logger.warning("Regex found no matches in content.")
        raise QuizError("No questions found. Please check the file format.")
    
    questions = []
    errors = []
    
    for i, match in enumerate(matches, start=1):
        try:
            question_text = match[0].strip()
            choices_text = match[1]
            answer_line = match[2].strip()
            
            # Parse choices
            choices = parse_choices(choices_text)
            
            # Extract answer letter
            answer_m = ANSWER_LETTER_RE.search(answer_line)
            if not answer_m:
                errors.append(f"Question {i}: No valid answer letter (A-D) found in '{answer_line}'")
                continue
            
            correct_letter = answer_m.group(1).upper()
            
            # Validate block
            is_valid, reason = validate_block(question_text, choices, correct_letter)
            
            if is_valid:
                questions.append({
                    'question': question_text,
                    'choices': choices,
                    'answer': correct_letter
                })
            else:
                errors.append(f"Question {i}: {reason}")
                
        except Exception as e:
            errors.append(f"Question {i}: Unexpected error during parsing - {str(e)}")

    if errors:
        for err in errors:
            logger.warning(err)
            
    if not questions:
        error_msg = "No valid questions could be parsed.\n" + "\n".join(errors[:5])
        if len(errors) > 5:
            error_msg += f"\n...and {len(errors) - 5} more errors."
        raise QuizError(error_msg)
        
    logger.info(f"Successfully parsed {len(questions)} questions.")
    return questions

def load_questions(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and parse questions from a file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_quiz_content(content)
    except FileNotFoundError:
        raise QuizError(f"File not found: {file_path}")
    except PermissionError:
        raise QuizError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        if isinstance(e, QuizError):
            raise
        raise QuizError(f"Error reading file: {str(e)}")

def load_questions_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse quiz questions directly from text string.
    """
    if not text or not text.strip():
        raise QuizError("Empty text provided")
    return parse_quiz_content(text)
