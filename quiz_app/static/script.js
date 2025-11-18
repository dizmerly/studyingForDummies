(function() {
'use strict';

// API Configuration
const API_BASE = '/api';

// Application state
let totalQuestions = 0;
let quizStartTime = null;
let keyboardShortcutsEnabled = false;

// Keyboard shortcuts functions
function enableKeyboardShortcuts() {
    keyboardShortcutsEnabled = true;
}

function disableKeyboardShortcuts() {
    keyboardShortcutsEnabled = false;
}

// Theme toggle
function toggleTheme() {
    document.body.classList.toggle('light-mode');
    localStorage.setItem('theme', document.body.classList.contains('light-mode') ? 'light' : 'dark');
}

// Load saved theme
window.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
    }
    loadHistoryFromStorage();
});

// Modal controls
function showHelp() {
    document.getElementById('helpModal').classList.add('active');
}

function closeHelpModal() {
    document.getElementById('helpModal').classList.remove('active');
}

function showPasteModal() {
    document.getElementById('pasteModal').classList.add('active');
}

function closePasteModal() {
    document.getElementById('pasteModal').classList.remove('active');
}

// File upload handler
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            totalQuestions = data.total_questions;
            quizStartTime = Date.now();
            await loadQuestion();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to upload file: ${error.message}`);
    }
}

// Submit pasted text
async function submitPastedText() {
    const text = document.getElementById('pasteTextarea').value.trim();
    if (!text) {
        alert('Please paste some text first!');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/paste`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            totalQuestions = data.total_questions;
            quizStartTime = Date.now();
            closePasteModal();
            document.getElementById('pasteTextarea').value = '';
            await loadQuestion();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to load quiz: ${error.message}`);
    }
}

// Screen navigation
function showScreen(screenId) {
    document.getElementById('startScreen').classList.add('hidden');
    document.getElementById('quizScreen').classList.add('hidden');
    document.getElementById('resultsScreen').classList.add('hidden');
    document.getElementById('historyScreen').classList.add('hidden');
    document.getElementById(screenId).classList.remove('hidden');
}

function showStartScreen() {
    loadNewQuiz();
}

function showHistoryScreen() {
    showScreen('historyScreen');
    loadHistoryFromStorage();
}

// Load and display current question from server
async function loadQuestion() {
    try {
        const response = await fetch(`${API_BASE}/question`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            displayQuestion(data);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to load question: ${error.message}`);
    }
}

// Display question on screen
function displayQuestion(data) {
    showScreen('quizScreen');

    // Update progress
    const progress = (data.current / data.total) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    document.getElementById('progressText').textContent = 
        `Question ${data.current} of ${data.total} | Score: ${data.score}/${data.current - 1}`;

    // Update question text
    document.getElementById('questionText').textContent = data.question;

    // Create choices
    const container = document.getElementById('choicesContainer');
    container.innerHTML = '';

    data.choices.forEach(([letter, text]) => {
        const choiceDiv = document.createElement('div');
        choiceDiv.className = 'choice';
        choiceDiv.onclick = () => selectChoice(letter, choiceDiv);

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'answer';
        radio.value = letter;
        radio.id = 'choice' + letter;

        const label = document.createElement('label');
        label.htmlFor = 'choice' + letter;
        label.textContent = `${letter}: ${text}`;
        label.style.cursor = 'pointer';
        label.style.flex = '1';

        choiceDiv.appendChild(radio);
        choiceDiv.appendChild(label);
        container.appendChild(choiceDiv);
    });

    document.getElementById('feedback').textContent = '';
    document.getElementById('feedback').className = 'feedback';
    
    // Enable keyboard shortcuts for this question
    enableKeyboardShortcuts();
}

// Select answer choice
function selectChoice(letter, choiceDiv) {
    document.querySelectorAll('.choice').forEach(c => c.classList.remove('selected'));
    choiceDiv.classList.add('selected');
    document.getElementById('choice' + letter).checked = true;
}

// Global keyboard event listener
document.addEventListener('keydown', (event) => {
    // Don't interfere with typing in textareas or inputs
    if (event.target.tagName === 'TEXTAREA' || event.target.tagName === 'INPUT') {
        return;
    }
    
    // Only work when quiz screen is active and shortcuts are enabled
    const quizScreen = document.getElementById('quizScreen');
    if (quizScreen.classList.contains('hidden') || !keyboardShortcutsEnabled) {
        return;
    }
    
    const key = event.key.toLowerCase();
    
    // Number keys 1-4 select choices A-D
    if (key >= '1' && key <= '4') {
        event.preventDefault();
        const letters = ['A', 'B', 'C', 'D'];
        const letter = letters[parseInt(key) - 1];
        const choiceElement = document.getElementById('choice' + letter);
        if (choiceElement) {
            const choiceDiv = choiceElement.closest('.choice');
            selectChoice(letter, choiceDiv);
        }
    }
    
    // Letter keys A-D also select choices
    if (key === 'a' || key === 'b' || key === 'c' || key === 'd') {
        event.preventDefault();
        const letter = key.toUpperCase();
        const choiceElement = document.getElementById('choice' + letter);
        if (choiceElement) {
            const choiceDiv = choiceElement.closest('.choice');
            selectChoice(letter, choiceDiv);
        }
    }
    
    // Enter or Space submits the answer
    if (key === 'enter' || key === ' ') {
        event.preventDefault();
        checkAnswer();
    }
});

// Check answer with server
async function checkAnswer() {
    const selectedRadio = document.querySelector('input[name="answer"]:checked');
    
    if (!selectedRadio) {
        const feedback = document.getElementById('feedback');
        feedback.textContent = 'Please select an answer';
        feedback.className = 'feedback warning';
        return;
    }

    const answer = selectedRadio.value;
    
    // Disable keyboard shortcuts while processing
    disableKeyboardShortcuts();

    try {
        const response = await fetch(`${API_BASE}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answer }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            const feedback = document.getElementById('feedback');

            // Highlight correct and incorrect answers
            const correctChoiceDiv = document.getElementById('choice' + data.correct_answer).closest('.choice');
            const selectedChoiceDiv = selectedRadio.closest('.choice');

            if (data.correct) {
                feedback.textContent = '✓ Correct!';
                feedback.className = 'feedback correct';
                selectedChoiceDiv.classList.add('correct-answer');
            } else {
                feedback.textContent = `✗ Incorrect. The correct answer is ${data.correct_answer}`;
                feedback.className = 'feedback incorrect';
                selectedChoiceDiv.classList.add('wrong-answer');
                correctChoiceDiv.classList.add('correct-answer');
            }

            setTimeout(async () => {
                if (data.has_more) {
                    await loadQuestion();
                } else {
                    await showResults();
                }
            }, 800);
        } else {
            alert(`Error: ${data.error}`);
            enableKeyboardShortcuts(); // Re-enable on error
        }
    } catch (error) {
        alert(`Failed to check answer: ${error.message}`);
        enableKeyboardShortcuts(); // Re-enable on error
    }
}

// Display final results from server
async function showResults() {
    try {
        const response = await fetch(`${API_BASE}/results`, {
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            showScreen('resultsScreen');

            document.getElementById('scoreText').textContent = `Your Score: ${data.score} / ${data.total}`;
            document.getElementById('percentageText').textContent = `${data.percentage}%`;

            let message;
            if (data.percentage >= 90) {
                message = "Excellent work! 🌟";
            } else if (data.percentage >= 70) {
                message = "Good job! 👍";
            } else if (data.percentage >= 50) {
                message = "Not bad! Keep practicing. 📚";
            } else {
                message = "Keep studying! You'll do better next time. 💪";
            }

            document.getElementById('messageText').textContent = message;

            // Save to history
            saveQuizToHistory(data);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to load results: ${error.message}`);
    }
}

// History management
function saveQuizToHistory(data) {
    const history = JSON.parse(localStorage.getItem('quizHistory') || '[]');
    
    const quizTime = quizStartTime ? Math.round((Date.now() - quizStartTime) / 1000) : 0;
    const minutes = Math.floor(quizTime / 60);
    const seconds = quizTime % 60;
    
    const entry = {
        date: new Date().toISOString(),
        score: data.score,
        total: data.total,
        percentage: data.percentage,
        duration: `${minutes}m ${seconds}s`
    };
    
    history.unshift(entry); // Add to beginning
    
    // Keep only last 20 entries
    if (history.length > 20) {
        history.pop();
    }
    
    localStorage.setItem('quizHistory', JSON.stringify(history));
}

function loadHistoryFromStorage() {
    const history = JSON.parse(localStorage.getItem('quizHistory') || '[]');
    const historyList = document.getElementById('historyList');
    const emptyState = document.getElementById('emptyHistory');
    
    historyList.innerHTML = '';
    
    if (history.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    history.forEach((entry, index) => {
        const date = new Date(entry.date);
        const dateStr = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
        
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div class="history-date">${dateStr}</div>
            <div class="history-score">${entry.percentage}% - ${entry.score}/${entry.total}</div>
            <div class="history-details">Completed in ${entry.duration}</div>
        `;
        
        historyList.appendChild(item);
    });
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all quiz history?')) {
        localStorage.removeItem('quizHistory');
        loadHistoryFromStorage();
    }
}

// Restart current quiz
async function restartQuiz() {
    try {
        const response = await fetch(`${API_BASE}/restart`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            quizStartTime = Date.now();
            await loadQuestion();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to restart quiz: ${error.message}`);
    }
}

// Load new quiz
async function loadNewQuiz() {
    try {
        const response = await fetch(`${API_BASE}/reset`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            showScreen('startScreen');
            quizStartTime = null;
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Failed to reset: ${error.message}`);
    }
}

// Make functions globally accessible for HTML onclick handlers
window.toggleTheme = toggleTheme;
window.showHelp = showHelp;
window.closeHelpModal = closeHelpModal;
window.showPasteModal = showPasteModal;
window.closePasteModal = closePasteModal;
window.handleFileUpload = handleFileUpload;
window.submitPastedText = submitPastedText;
window.showStartScreen = showStartScreen;
window.showHistoryScreen = showHistoryScreen;
window.checkAnswer = checkAnswer;
window.restartQuiz = restartQuiz;
window.loadNewQuiz = loadNewQuiz;
window.clearHistory = clearHistory;

})(); // End of IIFE wrapper