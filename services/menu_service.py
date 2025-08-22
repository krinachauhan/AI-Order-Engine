import json
from pathlib import Path
from typing import Any, Dict, List, Optional,Tuple
import requests
from rapidfuzz import process
from utils.config import MENU_API_URL
from utils.logger import get_logger
from utils.file_manager import write_json, read_json
from rapidfuzz import process

logger = get_logger(__name__)
MENU_DATA = Path("data/parsed_menu.json")



def find_price(item_name: str, size: Optional[str] = None) -> int:
    """
    Look up item price from parsed_menu.json.
    Uses fuzzy matching for item name and optional size.
    """
    menu = read_json(MENU_DATA)
    if not menu:
        return 0

    # First try exact match
    for item in menu:
        if item_name.lower() == item["ItemName"].lower():
            if size:
                for s in item.get("SizeListWidget", []):
                    if size.lower() == s["SizeName"].lower():
                        return s["Price"] or 0
            return item.get("Price", 0)

    # If exact match not found, use fuzzy matching
    names = [it["ItemName"] for it in menu]
    best, score, _ = process.extractOne(item_name, names)
    if score < 80:  # threshold
        return 0

    # Found fuzzy match → fetch price
    for item in menu:
        if item["ItemName"] == best:
            if size:
                for s in item.get("SizeListWidget", []):
                    if size.lower() == s["SizeName"].lower():
                        return s["Price"] or 0
            return item.get("Price", 0)

    return 0

def get_item_names():
    menu_data = read_json(MENU_DATA)
    if not menu_data:
        print("No menu data found!")
        return []
    
    item_names = [item["ItemName"] for item in menu_data if "ItemName" in item]
    return item_names

def fetch_menu_data() -> Dict[str, Any]:
    """Fetch raw menu data from API and parse JSON inside 'data' field."""
    logger.info("Fetching menu data from API...")
    try:
        response = requests.get(MENU_API_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch menu: {e}")
        raise

    raw_json = response.json()
    if "data" not in raw_json:
        raise ValueError("No 'data' field found in API response")

    try:
        menu_json = json.loads(raw_json["data"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format inside 'data' field: {e}")

    logger.info("Menu data fetched and parsed successfully.")
    return menu_json

def extract_required_items(menu_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract required fields from menu JSON into a clean list."""
    logger.info("Extracting required fields from menu data...")
    extracted_items = []

    for category in menu_json.get("CategoryList", []):
        category_id = category.get("CategryId")
        category_name = category.get("CategryName")

        for item in category.get("ItemListWidget", []):
            item_obj = {
                "ItemId": item.get("ItemId"),
                "ItemName": item.get("ItemName"),
                "Description": item.get("Description", ""),
                "Price": item.get("Price"),
                "SizeId": item.get("SizeId"),
                "SizeListWidget": [],
                "CategoryId": category_id,
                "CategoryName": category_name
            }

            for size in item.get("SizeListWidget", []):
                size_obj = {
                    "SizeId": size.get("SizeId"),
                    "SizeName": size.get("SizeName"),
                    "Price": size.get("Price")
                }
                item_obj["SizeListWidget"].append(size_obj)

            extracted_items.append(item_obj)

    logger.info(f"Extracted {len(extracted_items)} items from menu.")
    return extracted_items


def refresh_and_store_menu(file_path: Path = Path("data/parsed_menu.json")) -> List[Dict[str, Any]]:
    """Fetch menu from API, extract required data, and store in JSON file."""
    menu = fetch_menu_data()
    cleaned_menu = extract_required_items(menu)
    write_json(file_path, cleaned_menu)
    logger.info(f"Menu saved to {file_path}")
    return cleaned_menu

# if __name__ == "__main__":
#     refresh_and_store_menu()
#     names = get_item_names()
#     print("Extracted Item Names:")
#     for name in names:
#         print("-", name)