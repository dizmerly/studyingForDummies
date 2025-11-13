import re


print("this is the new file")
# ---------- helpers ----------
BLOCK_RE = re.compile(
    r'"""QUESTION"""\s*(.*?)\s*'
    r'"""CHOICES"""\s*(.*?)\s*'
    r'"""ANSWER"""\s*([A-D].*)',      # <- entire answer line
    re.DOTALL | re.I
)

def parse_choices(choices_text: str):
    """Return list [('A', text), ...]  (upper-case letters)."""
    return [(m.group(1).upper(), m.group(2).strip())
            for m in re.finditer(r'([A-D]):\s*(.+)', choices_text, re.I)]

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
file_path = input("Enter file name: ").strip()
with open(file_path, encoding="utf-8") as f:
    content = f.read()

matches = BLOCK_RE.findall(content)          # <- new regex
if not matches:
    print("No matches found")
    exit()

for i, match in enumerate(matches, start=1):
    question_text = match[0].strip()
    choices_text  = match[1]
    answer_line   = match[2].strip()

    # parse choices once
    choices = parse_choices(choices_text)

    # extract answer letter
    answer_m = re.search(r'\b([A-D])\b', answer_line, re.I)
    if not answer_m:                       # should never happen with BLOCK_RE
        print(f"Question {i} skipped – no answer letter.")
        continue
    correct_letter = answer_m.group(1).upper()

    # validate
    ok, reason = valid_block(question_text, choices, correct_letter)
    if not ok:
        print(f"Question {i} skipped – {reason}.")
        continue

    # ---------- quiz interaction ----------
    print(f"\nQuestion {i}: {question_text}")
    for letter, text in choices:
        print(f"{letter}: {text}")

    while True:
        user_ans = input("Your answer (A/B/C/D or Q to quit): ").strip().upper()
        if user_ans in {'A', 'B', 'C', 'D', 'Q'}:
            break
        print("Invalid choice. Please enter A, B, C, D, or Q.")

    if user_ans == 'Q':
        print("Quiz aborted.")
        break

    if user_ans == correct_letter:
        print("Correct!")
    else:
        print(f"Incorrect. Correct answer: {correct_letter}")
