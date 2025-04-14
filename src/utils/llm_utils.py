"""
LLM utilities module for the Recipe Substitution Search System.
This module provides functionality for using LLMs to generate ingredient substitutions.
"""

import os
import json
import sys
from typing import Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

# Import config
from src.utils.config import USE_LLM, LLM_MODEL_PATH, MODELS_DIR, PROCESSED_DATA_DIR

# Path to store the LLM-generated substitution database
LLM_SUBSTITUTION_DB_PATH = PROCESSED_DATA_DIR / "llm_substitution_db.json"

# Check if llama-cpp-python is available
try:
    from llama_cpp import Llama
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: llama-cpp-python not installed. LLM functions will be disabled.")
    print("To enable, install with: pip install llama-cpp-python")


def load_llm_model() -> Optional[object]:
    """
    Load the LLM model for substitution generation.
    
    Returns:
        Loaded LLM model or None if unavailable
    """
    if not USE_LLM or not LLM_AVAILABLE:
        return None
    
    # Check if model file exists
    if not os.path.exists(LLM_MODEL_PATH):
        print(f"LLM model file not found at: {LLM_MODEL_PATH}")
        return None
    
    try:
        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        # Load the model
        print(f"Loading LLM model from {LLM_MODEL_PATH}...")
        model = Llama(
            model_path=str(LLM_MODEL_PATH),
            n_ctx=2048,         # Context window size
            n_threads=4,        # Number of CPU threads to use
            n_gpu_layers=0      # Number of layers to offload to GPU (0 for CPU-only)
        )
        print("LLM model loaded successfully.")
        return model
        
    except Exception as e:
        print(f"Error loading LLM model: {e}")
        return None


def generate_substitutions(category: str, ingredient: str, model: Optional[object] = None) -> List[str]:
    """
    Generate substitutions for an ingredient using LLM.
    
    Args:
        category: Dietary restriction category
        ingredient: Ingredient to find substitutions for
        model: LLM model (if None, will attempt to load)
        
    Returns:
        List of substitution ingredients
    """
    if not model and LLM_AVAILABLE and USE_LLM:
        model = load_llm_model()
    
    if not model:
        # Fallback to pre-generated substitutions if no model available
        return get_fallback_substitutions(category, ingredient)
    
    # Craft prompt for substitution generation
    prompt = f"""
# Task: Generate ingredient substitutions for recipes
# Dietary restriction: {category}
# Ingredient to substitute: {ingredient}

Please provide a list of 5 suitable substitutes for {ingredient} that would work well in recipes 
requiring {category} dietary restrictions. For each substitute, consider taste profile, texture, 
and cooking properties to maintain the essence of the original dish.

List of {category} substitutes for {ingredient}:
1. """

    try:
        # Generate completions using the model
        output = model.create_completion(
            prompt=prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
            stop=["#", "List of"],  # Stop generation at these tokens
            echo=False
        )
        
        # Extract substitutions from the response
        completion_text = output["choices"][0]["text"]
        
        # Parse the response to extract substitutions
        substitutions = []
        for line in completion_text.strip().split("\n"):
            # Remove numbered list markers and any explanatory text
            if "." in line:
                sub = line.split(".", 1)[1].split("-")[0].split("(")[0].strip()
                if sub and len(sub) > 1:  # Ensure non-empty and reasonable length
                    substitutions.append(sub)
        
        # Ensure we have at least some substitutions
        if not substitutions and "," in completion_text:
            # Try parsing as comma-separated list
            substitutions = [s.strip() for s in completion_text.split(",")]
        
        # Return up to 5 substitutions
        return substitutions[:5]
        
    except Exception as e:
        print(f"Error generating substitutions with LLM: {e}")
        return get_fallback_substitutions(category, ingredient)


def get_fallback_substitutions(category: str, ingredient: str) -> List[str]:
    """
    Get fallback substitutions if LLM generation fails.
    
    Args:
        category: Dietary restriction category
        ingredient: Ingredient to find substitutions for
        
    Returns:
        List of substitution ingredients
    """
    # Try to load from pre-generated LLM substitutions
    if os.path.exists(LLM_SUBSTITUTION_DB_PATH):
        try:
            with open(LLM_SUBSTITUTION_DB_PATH, 'r') as f:
                substitution_db = json.load(f)
                
            if category in substitution_db and ingredient in substitution_db[category]:
                return substitution_db[category][ingredient]
        except Exception:
            pass
    
    # Fallback to basic substitutions by category
    basic_substitutions = {
        "vegetarian": ["tofu", "tempeh", "seitan", "beans", "lentils"],
        "vegan": ["tofu", "tempeh", "seitan", "nutritional yeast", "plant-based alternative"],
        "gluten-free": ["rice flour", "almond flour", "cornstarch", "gluten-free alternative", "potato starch"],
        "dairy-free": ["coconut milk", "almond milk", "cashew cream", "olive oil", "avocado"],
        "nut-free": ["seeds", "oats", "coconut", "dried fruits", "chocolate chips"]
    }
    
    return basic_substitutions.get(category, ["suitable alternative"])


def build_llm_substitution_database(save_to_file: bool = True) -> Dict[str, Dict[str, List[str]]]:
    """
    Build a comprehensive substitution database using LLM.
    
    Args:
        save_to_file: Whether to save the database to a file
        
    Returns:
        Dictionary of substitutions by category and ingredient
    """
    if not LLM_AVAILABLE or not USE_LLM:
        print("LLM not available. Cannot build substitution database.")
        return {}
    
    # Categories to cover
    categories = [
        "vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free"
    ]
    
    # Common ingredients by category that need substitution
    ingredients_by_category = {
        "vegetarian": [
            "chicken", "beef", "pork", "shrimp", "fish", 
            "bacon", "gelatin", "lard", "chicken broth"
        ],
        "vegan": [
            "milk", "butter", "cheese", "eggs", "cream", 
            "yogurt", "honey", "mayonnaise", "chicken",
            "beef", "fish", "gelatin"
        ],
        "gluten-free": [
            "flour", "bread", "pasta", "couscous", "barley",
            "rye", "wheat", "beer", "soy sauce"
        ],
        "dairy-free": [
            "milk", "butter", "cheese", "cream", "yogurt",
            "ice cream", "sour cream", "custard", "whipped cream"
        ],
        "nut-free": [
            "almonds", "walnuts", "peanuts", "cashews", "pecans",
            "almond milk", "almond flour", "peanut butter", "nutella"
        ]
    }
    
    # Load model once for all generations
    model = load_llm_model()
    if not model:
        print("Failed to load LLM model. Cannot build substitution database.")
        return {}
    
    # Initialize substitution database
    substitution_db = {}
    
    # Generate substitutions for each category and ingredient
    for category in categories:
        print(f"Generating substitutions for {category} recipes...")
        substitution_db[category] = {}
        
        for ingredient in ingredients_by_category.get(category, []):
            print(f"  - Finding substitutes for {ingredient}...")
            substitutes = generate_substitutions(category, ingredient, model)
            
            if substitutes:
                substitution_db[category][ingredient] = substitutes
                print(f"    Found: {', '.join(substitutes)}")
            else:
                print(f"    No substitutes found.")
    
    # Save to file if requested
    if save_to_file:
        os.makedirs(os.path.dirname(LLM_SUBSTITUTION_DB_PATH), exist_ok=True)
        with open(LLM_SUBSTITUTION_DB_PATH, 'w') as f:
            json.dump(substitution_db, f, indent=2)
        print(f"Saved LLM-generated substitution database to {LLM_SUBSTITUTION_DB_PATH}")
    
    return substitution_db


def create_dummy_llm_substitutions() -> Dict[str, Dict[str, List[str]]]:
    """
    Create a dummy LLM substitution database for testing.
    
    Returns:
        Dictionary of dummy substitutions
    """
    print("Creating dummy LLM-generated substitution database...")
    
    substitution_db = {
        "vegetarian": {
            "chicken": ["tofu", "seitan", "tempeh", "jackfruit", "chickpeas"],
            "beef": ["lentils", "mushrooms", "tempeh", "plant-based beef", "seitan"],
            "pork": ["jackfruit", "tempeh", "seitan", "mushrooms", "plant-based pork"],
            "fish": ["tofu", "tempeh", "hearts of palm", "seaweed", "chickpeas"],
            "bacon": ["tempeh bacon", "coconut bacon", "mushroom bacon", "rice paper bacon", "seitan bacon"],
            "gelatin": ["agar-agar", "carrageenan", "pectin", "fruit pectin", "vegetable gum"]
        },
        "vegan": {
            "milk": ["almond milk", "soy milk", "oat milk", "coconut milk", "rice milk"],
            "butter": ["vegan butter", "coconut oil", "olive oil", "avocado", "nut butter"],
            "cheese": ["nutritional yeast", "vegan cheese", "cashew cheese", "tofu", "vegan cream cheese"],
            "eggs": ["flax egg", "chia egg", "applesauce", "banana", "silken tofu"],
            "honey": ["maple syrup", "agave nectar", "date syrup", "brown rice syrup", "coconut nectar"]
        },
        "gluten-free": {
            "flour": ["almond flour", "rice flour", "coconut flour", "chickpea flour", "gluten-free blend"],
            "bread": ["gluten-free bread", "corn bread", "rice bread", "potato bread", "cassava bread"],
            "pasta": ["rice pasta", "chickpea pasta", "zucchini noodles", "corn pasta", "quinoa pasta"],
            "soy sauce": ["tamari", "coconut aminos", "liquid aminos", "fish sauce", "salt"],
            "beer": ["gluten-free beer", "cider", "wine", "mead", "sake"]
        },
        "dairy-free": {
            "milk": ["almond milk", "soy milk", "oat milk", "coconut milk", "rice milk"],
            "butter": ["coconut oil", "olive oil", "vegan butter", "avocado", "nut butter"],
            "cheese": ["nutritional yeast", "vegan cheese", "cashew cheese", "tofu", "avocado"],
            "cream": ["coconut cream", "cashew cream", "silken tofu", "almond cream", "oat cream"],
            "yogurt": ["coconut yogurt", "soy yogurt", "almond yogurt", "cashew yogurt", "oat yogurt"]
        },
        "nut-free": {
            "almonds": ["sunflower seeds", "pumpkin seeds", "hemp seeds", "watermelon seeds", "coconut"],
            "peanut butter": ["sunflower seed butter", "pumpkin seed butter", "tahini", "coconut butter", "soy nut butter"],
            "almond milk": ["oat milk", "coconut milk", "rice milk", "flax milk", "hemp milk"],
            "cashews": ["sunflower seeds", "pumpkin seeds", "hemp seeds", "watermelon seeds", "coconut"],
            "pecans": ["sunflower seeds", "pumpkin seeds", "hemp seeds", "watermelon seeds", "coconut"]
        }
    }
    
    # Save to file
    os.makedirs(os.path.dirname(LLM_SUBSTITUTION_DB_PATH), exist_ok=True)
    with open(LLM_SUBSTITUTION_DB_PATH, 'w') as f:
        json.dump(substitution_db, f, indent=2)
    
    print(f"Saved dummy LLM-generated substitution database to {LLM_SUBSTITUTION_DB_PATH}")
    return substitution_db


if __name__ == "__main__":
    # If run as a script, create dummy LLM substitutions
    create_dummy_llm_substitutions() 