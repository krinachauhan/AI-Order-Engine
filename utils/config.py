import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if exists)
load_dotenv()

# ====================
# API CONFIGURATION
# ====================

# Menu API
SHOP_ID = os.getenv("SHOP_ID", "1833")  # Default to 3161 if not set

# Construct the full API URL using the dynamic shop_id
MENU_API_URL = f"https://www.foodchow.com/api/FoodChowWD/GetRestaurantMenuForPOSWithSoldOut?shop_id={SHOP_ID}"