import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass

def generate_quiz_from_notes(notes_text: str, api_key: str, num_questions: int = 10, difficulty: str = "medium") -> str:
    """
    Generate quiz questions from study notes using OpenAI.
    
    Args:
        notes_text: Raw study notes text
        api_key: User's OpenAI API key
        num_questions: Number of questions to generate
        difficulty: Question difficulty (easy, medium, hard)
        
    Returns:
        Formatted quiz text in the expected format
        
    Raises:
        AIServiceError: If generation fails
    """
    try:
        client = OpenAI(api_key=api_key)
        
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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful quiz generator that creates well-formatted multiple choice questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        quiz_text = response.choices[0].message.content.strip()
        
        # Validate that we got something
        if not quiz_text or '"""QUESTION"""' not in quiz_text:
            raise AIServiceError("Generated quiz is not in the correct format")
        
        logger.info(f"Successfully generated {num_questions} questions using AI")
        return quiz_text
        
    except Exception as e:
        logger.error(f"AI quiz generation failed: {str(e)}")
        if "api_key" in str(e).lower() or "authentication" in str(e).lower():
            raise AIServiceError("Invalid API key. Please check your OpenAI API key in settings.")
        elif "rate_limit" in str(e).lower():
            raise AIServiceError("Rate limit exceeded. Please try again later.")
        elif "insufficient_quota" in str(e).lower():
            raise AIServiceError("API quota exceeded. Please check your OpenAI account.")
        else:
            raise AIServiceError(f"Failed to generate quiz: {str(e)}")


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
