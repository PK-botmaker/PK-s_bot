import re
from typing import List, Dict

def calculate_score(query: str, filename: str) -> float:
    """
    Calculate a weighted score for a file based on the search query. 📊
    Weights:
    - Exact match: 100 ✅
    - Word match: 20 per word 🔡
    - Partial match: 5 per character overlap 🔤
    """
    query = query.lower().strip()
    filename = filename.lower()

    score = 0.0

    # Exact match 🎯
    if query == filename:
        return 100.0

    # Split query into words 🔠
    query_words = set(re.split(r"\W+", query))
    filename_words = set(re.split(r"\W+", filename))

    # Word matches 🔡
    common_words = query_words.intersection(filename_words)
    score += len(common_words) * 20

    # Partial matches (character overlap) 🔤
    for q_word in query_words:
        for f_word in filename_words:
            if q_word in f_word or f_word in q_word:
                overlap = len(set(q_word).intersection(set(f_word)))
                score += overlap * 5

    return score

def search_files(query: str, files: List[Dict], limit: int = 5) -> List[Dict]:
    """
    Search for files matching the query using weighted scoring. 🔍
    """
    if not query or not files:
        return []

    # Calculate scores for each file 📊
    scored_files = []
    for file in files:
        filename = file.get("filename", "")
        if not filename:
            continue

        score = calculate_score(query, filename)
        if score > 0:
            scored_files.append((score, file))

    # Sort by score in descending order 📉
    scored_files.sort(key=lambda x: x[0], reverse=True)

    # Return top results 🏆
    return [file for _, file in scored_files[:limit]]