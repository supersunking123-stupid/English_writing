"""
Prompt templates for answer evaluation.
"""

from typing import List, Dict, Any


def get_evaluation_prompt(questions: List[Dict[str, Any]], user_answers: List[str]) -> tuple:
    """
    Generate prompts for evaluating student answers.

    Args:
        questions: List of question dictionaries
        user_answers: List of user's answers

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = """You are a patient English teacher responsible for evaluating student performance and providing constructive feedback. You must return valid JSON format only."""

    # Format questions and answers
    qa_pairs = []
    for i, (q, ans) in enumerate(zip(questions, user_answers), 1):
        qa_pairs.append(f"""Question {i} ({q['type']}):
Q: {q['question']}
Correct Answer: {q['correct_answer']}
Student Answer: {ans}
""")

    qa_text = "\n".join(qa_pairs)

    user_prompt = f"""Please evaluate the following answers:

{qa_text}

Requirements:
1. Give a total score (out of 100)
2. Analyze each question (correct/incorrect)
3. Explain why answers are wrong
4. Provide learning suggestions

Return in JSON format:
{{
  "score": 80,
  "item_analysis": [
    {{
      "question_num": 1,
      "correct": true,
      "feedback": "explanation"
    }}
  ],
  "overall_feedback": "overall evaluation",
  "suggestions": "learning suggestions"
}}

IMPORTANT: Return ONLY valid JSON, no other text."""

    return system_prompt, user_prompt
