from fastapi import APIRouter
from services.menu_service import refresh_and_store_menu, get_item_names

router = APIRouter()

@router.get("/menu/refresh")
def refresh_menu():
    data = refresh_and_store_menu()
    return {"message": "Menu updated", "total_items": len(data)}

@router.get("/menu/items")
def list_items():   
    return {"items": get_item_names()}
