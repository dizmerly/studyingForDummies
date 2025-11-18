from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import json
from quiz_logic import load_questions, load_questions_from_text
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

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='127.0.0.1')