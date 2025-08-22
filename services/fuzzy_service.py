from typing import Tuple, List, Dict, Any
from fuzzywuzzy import process, fuzz
from utils.file_manager import read_json, MENU_DATA
from typing import Tuple, Dict, Any, List
from rapidfuzz import fuzz, process

def fuzzy_match_item(query: str, high_threshold: int = 96, low_threshold: int = 80) -> Tuple[str, str, List[str]]:
    """
    Fuzzy match a user-provided item name against menu items.

    Returns a tuple:
      (status, best_match, suggestions)

    - status = "high_confidence" → use best_match silently
    - status = "suggest" → ask user to confirm from suggestions
    - status = "none" → no good match found
    """
    menu = read_json(MENU_DATA)
    if not menu:
        return "none", "", []

    names = [it["ItemName"] for it in menu]
    results = process.extract(query, names, limit=3)  # top 3 matches

    if not results:
        return "none", "", []

    best, score, _ = results[0]

    if score >= high_threshold:
        return "high_confidence", best, []
    elif score >= low_threshold:
        suggestions = [name for name, s, _ in results if s >= low_threshold]
        return "suggest", best, suggestions
    else:
        return "none", "", []