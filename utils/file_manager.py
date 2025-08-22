from pathlib import Path
from typing import Any, Union
import json

MENU_DATA = Path("data/parsed_menu.json")

def write_json(file_path: Union[str, Path], data: Any) -> None:
    """Write Python data to a JSON file with UTF-8 encoding."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read_json(file_path: Union[str, Path]) -> Any:
    """Read JSON data from file."""
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def append_json(file_path: str, new_data: dict):
    path = Path(file_path)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    data.append(new_data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
