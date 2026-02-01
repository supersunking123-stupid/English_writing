"""
Prompt templates for article and question generation.
"""

from typing import List


def get_article_generation_prompt(words: List[str], age: int, lexile: int) -> tuple:
    """
    Generate prompts for article and question creation.

    Args:
        words: List of words to include
        age: User's age
        lexile: User's Lexile level

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are a professional English teacher who excels at creating appropriate reading materials for beginners. You must return valid JSON format only."""

    words_str = ", ".join(words[:50])  # Limit to first 50 words to avoid too long prompt
    if len(words) > 50:
        words_str += f" (and {len(words) - 50} more words)"

    user_prompt = f"""Please generate an English reading article and 5 test questions based on the following information:

User Information:
- Age: {age} years old
- Lexile Level: {lexile} (grammar and sentence complexity indicator)

Word Bank: {words_str}

Requirements:
1. Article length: 150-250 words
2. Must use at least 80% of the words from the word bank
3. Grammar difficulty should match the Lexile level
4. Content should be age-appropriate, interesting, and educational

5 Test Questions Requirements:
- 2 multiple choice questions (4 options A/B/C/D)
- 2 fill-in-the-blank questions (test vocabulary and grammar)
- 1 true/false question

Please return in JSON format:
{{
  "article": "article content here",
  "questions": [
    {{
      "type": "multiple_choice",
      "question": "question text",
      "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
      "correct_answer": "A"
    }},
    {{
      "type": "fill_blank",
      "question": "question text (use ___ for blank)",
      "correct_answer": "answer"
    }},
    {{
      "type": "true_false",
      "question": "question text",
      "correct_answer": true
    }}
  ]
}}

IMPORTANT: Return ONLY valid JSON, no other text."""

    return system_prompt, user_prompt
