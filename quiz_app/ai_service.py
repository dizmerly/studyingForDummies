import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


def detect_provider(api_key: str) -> str:
    """Detect which LLM provider based on API key format."""
    if api_key.startswith('sk-'):
        return 'openai'
    elif api_key.startswith('sk-ant-'):
        return 'anthropic'
    elif api_key.startswith('AIza'):
        return 'google'
    elif api_key == 'ollama' or api_key.startswith('ollama'):
        return 'ollama'
    else:
        return 'openai'  # Default to OpenAI


def generate_quiz_from_notes(notes_text: str, api_key: str, num_questions: int = 10, difficulty: str = "medium", provider: str = None) -> str:
    """
    Generate quiz questions from study notes using AI.
    
    Args:
        notes_text: Raw study notes text
        api_key: User's API key (OpenAI, Claude, Gemini, or 'ollama')
        num_questions: Number of questions to generate
        difficulty: Question difficulty (easy, medium, hard)
        provider: LLM provider ('openai', 'anthropic', 'google', 'ollama')
        
    Returns:
        Formatted quiz text in the expected format
        
    Raises:
        AIServiceError: If generation fails
    """
    try:
        # Auto-detect provider if not specified
        if provider is None:
            provider = detect_provider(api_key)
        
        difficulty_instructions = {
            "easy": "straightforward recall questions",
            "medium": "questions requiring understanding and application",
            "hard": "complex questions requiring analysis and synthesis"
        }
        
        prompt = f"""You are a quiz generator. Generate {num_questions} multiple choice questions from the following study notes.

Study Notes:
{notes_text}

Requirements:
- Create {difficulty_instructions.get(difficulty, 'medium difficulty')} questions
- Each question must have exactly 4 choices (A, B, C, D)
- Only one correct answer per question
- Questions should test understanding of the material
- Use the EXACT format below (this is critical):

\"\"\"QUESTION\"\"\"
[Your question here]
\"\"\"CHOICES\"\"\"
A: [First choice]
B: [Second choice]
C: [Third choice]
D: [Fourth choice]
\"\"\"ANSWER\"\"\"
[Correct letter only, e.g., A]

Generate {num_questions} questions following this exact format. Do not include any other text or explanations."""

        # Generate based on provider
        if provider == 'openai':
            quiz_text = _generate_with_openai(api_key, prompt)
        elif provider == 'anthropic':
            quiz_text = _generate_with_claude(api_key, prompt)
        elif provider == 'google':
            quiz_text = _generate_with_gemini(api_key, prompt)
        elif provider == 'ollama':
            quiz_text = _generate_with_ollama(prompt)
        else:
            raise AIServiceError(f"Unsupported provider: {provider}")
        
        # Validate that we got something
        if not quiz_text or '"""QUESTION"""' not in quiz_text:
            raise AIServiceError("Generated quiz is not in the correct format")
        
        logger.info(f"Successfully generated {num_questions} questions using {provider}")
        return quiz_text
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"AI quiz generation failed: {str(e)}")
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            raise AIServiceError("Invalid API key. Please check your API key in settings.")
        elif "rate_limit" in str(e).lower():
            raise AIServiceError("Rate limit exceeded. Please try again later.")
        elif "insufficient_quota" in str(e).lower():
            raise AIServiceError("API quota exceeded. Please check your account.")
        else:
            raise AIServiceError(f"Failed to generate quiz: {str(e)}")


def _generate_with_openai(api_key: str, prompt: str) -> str:
    """Generate quiz using OpenAI API."""
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful quiz generator that creates well-formatted multiple choice questions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content.strip()


def _generate_with_claude(api_key: str, prompt: str) -> str:
    """Generate quiz using Anthropic Claude API."""
    try:
        import anthropic
    except ImportError:
        raise AIServiceError("Anthropic library not installed. Run: pip install anthropic")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text.strip()


def _generate_with_gemini(api_key: str, prompt: str) -> str:
    """Generate quiz using Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise AIServiceError("Google AI library not installed. Run: pip install google-generativeai")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    response = model.generate_content(prompt)
    return response.text.strip()


def _generate_with_ollama(prompt: str) -> str:
    """Generate quiz using local Ollama."""
    try:
        import requests
    except ImportError:
        raise AIServiceError("Requests library not installed")
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2',
                'prompt': prompt,
                'stream': False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()['response'].strip()
        else:
            raise AIServiceError(f"Ollama error: {response.text}")
    except requests.exceptions.ConnectionError:
        raise AIServiceError("Cannot connect to Ollama. Make sure Ollama is running (ollama serve)")
    except requests.exceptions.Timeout:
        raise AIServiceError("Ollama request timed out. Try a smaller number of questions.")



def chat_with_assistant(user_message: str, context: Optional[str], api_key: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Chat with AI study assistant.
    
    Args:
        user_message: User's question or message
        context: Study notes or quiz context
        api_key: User's OpenAI API key
        conversation_history: Previous messages in conversation
        
    Returns:
        Dict with 'response' and 'updated_history'
        
    Raises:
        AIServiceError: If chat fails
    """
    try:
        client = OpenAI(api_key=api_key)
        
        # Build conversation history
        messages = [
            {"role": "system", "content": """You are a helpful study assistant. Your role is to:
- Answer questions about the study material
- Explain concepts clearly and concisely
- Provide examples when helpful
- Encourage learning and understanding
- Be supportive and patient

Keep responses concise but informative."""}
        ]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "system",
                "content": f"Here is the study material for reference:\n\n{context[:2000]}"  # Limit context size
            })
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        assistant_response = response.choices[0].message.content.strip()
        
        # Update history
        updated_history = (conversation_history or []) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_response}
        ]
        
        # Keep only last 10 messages to avoid token limits
        if len(updated_history) > 10:
            updated_history = updated_history[-10:]
        
        logger.info("AI assistant response generated successfully")
        return {
            "response": assistant_response,
            "updated_history": updated_history
        }
        
    except Exception as e:
        logger.error(f"AI chat failed: {str(e)}")
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            raise AIServiceError("Invalid API key. Please check your OpenAI API key in settings.")
        elif "rate_limit" in str(e).lower():
            raise AIServiceError("Rate limit exceeded. Please try again later.")
        else:
            raise AIServiceError(f"Failed to get response: {str(e)}")
