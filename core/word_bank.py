"""
Word bank management module for loading, saving, and deduplicating words.
"""

from pathlib import Path
from typing import List, Set
from config import USERS_DIR, WORD_BANK_FILE


def load_words(username: str) -> List[str]:
    """
    Load words from user's word bank.

    Args:
        username: The username

    Returns:
        List of words
    """
    word_file = USERS_DIR / username / WORD_BANK_FILE

    if not word_file.exists():
        return []

    with open(word_file, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    return words


def save_words(username: str, words: List[str]) -> bool:
    """
    Save words to user's word bank.

    Args:
        username: The username
        words: List of words to save

    Returns:
        True if saved successfully
    """
    word_file = USERS_DIR / username / WORD_BANK_FILE

    with open(word_file, 'w', encoding='utf-8') as f:
        for word in words:
            if word.strip():
                f.write(f"{word.strip()}\n")

    return True


def deduplicate_words(username: str) -> int:
    """
    Remove duplicate words from user's word bank.

    Args:
        username: The username

    Returns:
        Number of words removed
    """
    words = load_words(username)
    original_count = len(words)

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in seen:
            seen.add(word_lower)
            unique_words.append(word)

    save_words(username, unique_words)

    return original_count - len(unique_words)


def add_words(username: str, new_words: List[str]) -> int:
    """
    Add new words to user's word bank.

    Args:
        username: The username
        new_words: List of new words to add

    Returns:
        Number of new words added (excluding duplicates)
    """
    existing_words = load_words(username)
    existing_set = {w.lower() for w in existing_words}

    added_count = 0
    for word in new_words:
        word = word.strip()
        if word and word.lower() not in existing_set:
            existing_words.append(word)
            existing_set.add(word.lower())
            added_count += 1

    save_words(username, existing_words)

    return added_count


def get_word_count(username: str) -> int:
    """
    Get the number of words in user's word bank.

    Args:
        username: The username

    Returns:
        Number of words
    """
    return len(load_words(username))
