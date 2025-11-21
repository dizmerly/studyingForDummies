from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
from quiz_logic import load_questions, load_questions_from_text, QuizError
from database import (create_user, authenticate_user, save_quiz_result, get_user_history,
                      save_api_key, get_api_key, has_api_key, delete_api_key)
from ai_service import generate_quiz_from_notes, chat_with_assistant, AIServiceError
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-to-something-random'

# Session configuration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_TYPE'] = 'filesystem'

# Enable CORS - Allow all origins for development
CORS(app, 
     supports_credentials=True, 
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

# Configuration
UPLOAD_FOLDER = './uploads'
USERDATA_FOLDER = './userdata'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USERDATA_FOLDER, exist_ok=True)

PREF_FILE = os.path.join(USERDATA_FOLDER, 'prefs.json')

def load_prefs():
    if os.path.exists(PREF_FILE):
        try:
            with open(PREF_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_prefs(prefs):
    try:
        with open(PREF_FILE, 'w') as f:
            json.dump(prefs, f)
        return True
    except:
        return False

# Authentication Routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Create a new user account."""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    result = create_user(email, password)
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['email'] = result['email']
        return jsonify({
            'success': True,
            'user': {'id': result['user_id'], 'email': result['email']}
        })
    else:
        return jsonify({'error': result['message']}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate a user."""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    result = authenticate_user(email, password)
    
    if result['success']:
        session['user_id'] = result['user_id']
        session['email'] = result['email']
        return jsonify({
            'success': True,
            'user': {'id': result['user_id'], 'email': result['email']}
        })
    else:
        return jsonify({'error': result['message']}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get the current logged-in user."""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {'id': session['user_id'], 'email': session['email']}
        })
    else:
        return jsonify({'authenticated': False})

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get quiz history for the current user."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    history = get_user_history(session['user_id'])
    return jsonify({'history': history})

# Routes
@app.route('/', methods=['GET'])
def index():
    """Serve the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error loading page: {str(e)}", 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    """Handle file upload and parse questions"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file temporarily
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        # Load questions using your existing function
        questions = load_questions(filepath)
        
        # Clean up temp file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if not questions:
            return jsonify({'error': 'No valid questions found'}), 400
        
        # Store questions in session
        session['questions'] = questions
        session['current_question'] = 0
        session['score'] = 0
        
        return jsonify({
            'success': True,
            'total_questions': len(questions)
        })
    
    except QuizError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/paste', methods=['POST', 'OPTIONS'])
def paste_text():
    """Handle pasted quiz text"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Load questions using your existing function
        questions = load_questions_from_text(text)
        
        if not questions:
            return jsonify({'error': 'No valid questions found'}), 400
        
        # Store questions in session
        session['questions'] = questions
        session['current_question'] = 0
        session['score'] = 0
        
        return jsonify({
            'success': True,
            'total_questions': len(questions)
        })
    
    except QuizError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/question', methods=['GET', 'OPTIONS'])
def get_question():
    """Get current question"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        questions = session.get('questions', [])
        current = session.get('current_question', 0)
        
        if not questions or current >= len(questions):
            return jsonify({'error': 'No questions available'}), 400
        
        question = questions[current]
        
        return jsonify({
            'question': question['question'],
            'choices': question['choices'],
            'current': current + 1,
            'total': len(questions),
            'score': session.get('score', 0)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/answer', methods=['POST', 'OPTIONS'])
def check_answer():
    """Check submitted answer"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        user_answer = data.get('answer', '')
        
        questions = session.get('questions', [])
        current = session.get('current_question', 0)
        score = session.get('score', 0)
        
        if not questions or current >= len(questions):
            return jsonify({'error': 'No question available'}), 400
        
        question = questions[current]
        correct = question['answer']
        is_correct = user_answer == correct
        
        if is_correct:
            score += 1
            session['score'] = score
        
        # Move to next question
        session['current_question'] = current + 1
        
        has_more = (current + 1) < len(questions)
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct,
            'score': score,
            'has_more': has_more
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET', 'OPTIONS'])
def get_results():
    """Get final quiz results"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        questions = session.get('questions', [])
        score = session.get('score', 0)
        total = len(questions)
        
        if total == 0:
            return jsonify({'error': 'No quiz data'}), 400
        
        percentage = (score / total) * 100
        
        return jsonify({
            'score': score,
            'total': total,
            'percentage': round(percentage, 1)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart', methods=['POST', 'OPTIONS'])
def restart_quiz():
    """Restart the current quiz"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        session['current_question'] = 0
        session['score'] = 0
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST', 'OPTIONS'])
def reset_quiz():
    """Reset everything and go back to start"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        session.clear()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prefs', methods=['GET', 'POST', 'OPTIONS'])
def preferences():
    """Get or set user preferences"""
    if request.method == 'OPTIONS':
        return '', 204
        
    if request.method == 'GET':
        prefs = load_prefs()
        return jsonify(prefs)
    else:
        data = request.get_json()
        if save_prefs(data):
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to save preferences'}), 500


# API Key Management Routes
@app.route('/api/settings/api-key', methods=['POST'])
def save_user_api_key():
    """Save user's OpenAI API key."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    api_key = data.get('apiKey', '').strip()
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    
    if not api_key.startswith('sk-'):
        return jsonify({'error': 'Invalid API key format'}), 400
    
    success = save_api_key(session['user_id'], api_key)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to save API key'}), 500


@app.route('/api/settings/api-key', methods=['GET'])
def check_user_api_key():
    """Check if user has API key configured."""
    if 'user_id' not in session:
        return jsonify({'hasKey': False})
    
    has_key = has_api_key(session['user_id'])
    return jsonify({'hasKey': has_key})


@app.route('/api/settings/api-key', methods=['DELETE'])
def delete_user_api_key():
    """Delete user's API key."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    success = delete_api_key(session['user_id'])
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to delete API key'}), 500


# AI Generation Routes
@app.route('/api/ai/generate-quiz', methods=['POST'])
def ai_generate_quiz():
    """Generate quiz from notes using AI."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user's API key
    api_key = get_api_key(session['user_id'])
    if not api_key:
        return jsonify({'error': 'No API key configured. Please add your OpenAI API key in settings.'}), 400
    
    data = request.get_json()
    notes = data.get('notes', '').strip()
    num_questions = data.get('numQuestions', 10)
    difficulty = data.get('difficulty', 'medium')
    
    if not notes:
        return jsonify({'error': 'Notes are required'}), 400
    
    try:
        # Generate quiz using AI
        quiz_text = generate_quiz_from_notes(notes, api_key, num_questions, difficulty)
        
        # Parse the generated quiz
        questions = load_questions_from_text(quiz_text)
        
        # Store in session
        session['questions'] = questions
        session['current_index'] = 0
        session['score'] = 0
        session['answers'] = []
        
        return jsonify({
            'success': True,
            'totalQuestions': len(questions)
        })
    except AIServiceError as e:
        return jsonify({'error': str(e)}), 400
    except QuizError as e:
        return jsonify({'error': f'Quiz validation failed: {str(e)}'}), 400
    except Exception as e:
        logging.error(f"AI quiz generation error: {str(e)}")
        return jsonify({'error': 'Failed to generate quiz. Please try again.'}), 500


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat with AI study assistant."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user's API key
    api_key = get_api_key(session['user_id'])
    if not api_key:
        return jsonify({'error': 'No API key configured'}), 400
    
    data = request.get_json()
    message = data.get('message', '').strip()
    context = data.get('context', '')
    history = data.get('history', [])
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        result = chat_with_assistant(message, context, api_key, history)
        return jsonify({
            'success': True,
            'response': result['response'],
            'history': result['updated_history']
        })
    except AIServiceError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logging.error(f"AI chat error: {str(e)}")
        return jsonify({'error': 'Failed to get response. Please try again.'}), 500


# if __name__ == '__main__':
#     app.run(debug=True, port=5001, host='127.0.0.1')
if __name__ == '__main__':
    # Render uses PORT environment variable
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
# gunicorn app:app 
# python3 app.py