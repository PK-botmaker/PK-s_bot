import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def search_files(query: str, files: List[Dict], limit: int = 5) -> List[Dict]:
    """
    Search for files matching the query with AI-like logic. 🔍
    Scores files based on exact match, word match, and partial match.
    """
    if not query or not files:
        return []

    query = query.lower().strip()
    scored_files = []

    for file in files:
        filename = file.get("filename", "").lower()
        if not filename:
            continue

        score = 0

        # Exact match (highest score) 🎯
        if query == filename:
            score += 100
        else:
            # Word match (split query and filename into words) 📝
            query_words = set(query.split())
            filename_words = set(filename.split())
            common_words = query_words.intersection(filename_words)
            score += len(common_words) * 20

            # Partial match (check if query is a substring of filename) 🔡
            if query in filename:
                score += 10

        if score > 0:
            scored_files.append((file, score))

    # Sort by score in descending order and limit results 📊
    scored_files.sort(key=lambda x: x[1], reverse=True)
    return [file for file, score in scored_files[:limit]]
