import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet

DATABASE_PATH = 'quiz_app.db'

# Encryption key for API keys - in production, use environment variable
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
cipher_suite = Fernet(ENCRYPTION_KEY)

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Quiz history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            duration TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # API keys table (encrypted)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            encrypted_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, password: str) -> Dict[str, Any]:
    """
    Create a new user account.
    
    Returns:
        Dict with 'success' boolean and 'message' or 'user_id'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': 'Email already registered'}
        
        # Create user
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (email, password_hash) VALUES (?, ?)',
            (email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'user_id': user_id, 'email': email}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user.
    
    Returns:
        Dict with 'success' boolean and 'message' or 'user_id'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            'SELECT id, email FROM users WHERE email = ? AND password_hash = ?',
            (email, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {'success': True, 'user_id': user['id'], 'email': user['email']}
        else:
            return {'success': False, 'message': 'Invalid email or password'}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def save_quiz_result(user_id: int, score: int, total: int, percentage: float, duration: str):
    """Save a quiz result to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO quiz_history (user_id, score, total, percentage, duration) VALUES (?, ?, ?, ?, ?)',
            (user_id, score, total, percentage, duration)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving quiz result: {e}")
        return False

def get_user_history(user_id: int) -> list:
    """Get quiz history for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT score, total, percentage, duration, completed_at FROM quiz_history WHERE user_id = ? ORDER BY completed_at DESC LIMIT 20',
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    except Exception as e:
        print(f"Error getting user history: {e}")
        return []


def save_api_key(user_id: int, api_key: str) -> bool:
    """Save encrypted API key for a user."""
    try:
        encrypted_key = cipher_suite.encrypt(api_key.encode()).decode()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys (user_id, encrypted_key, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                encrypted_key = excluded.encrypted_key,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, encrypted_key))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False


def get_api_key(user_id: int) -> Optional[str]:
    """Get decrypted API key for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT encrypted_key FROM api_keys WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            encrypted_key = result['encrypted_key']
            decrypted_key = cipher_suite.decrypt(encrypted_key.encode()).decode()
            return decrypted_key
        return None
    except Exception as e:
        print(f"Error getting API key: {e}")
        return None


def has_api_key(user_id: int) -> bool:
    """Check if user has an API key configured."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM api_keys WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    except Exception as e:
        print(f"Error checking API key: {e}")
        return False


def delete_api_key(user_id: int) -> bool:
    """Delete API key for a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM api_keys WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting API key: {e}")
        return False

# Initialize database on import
init_db()
