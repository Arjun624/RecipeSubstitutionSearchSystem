"""
Substitution database module for the Recipe Substitution Search System.
This module provides functionality to manage and access ingredient substitutions,
including integration with LLM-generated substitution mappings.
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from pathlib import Path

# Import config
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.utils.config import PROCESSED_DATA_DIR, USE_LLM, LLM_MODEL_PATH

# Path to store the substitution database
SUBSTITUTION_DB_PATH = PROCESSED_DATA_DIR / "substitution_db.json"

# Base substitution mappings for common dietary restrictions
# These will be expanded using LLM-generated suggestions
BASE_SUBSTITUTIONS = {
    "vegetarian": {
        "chicken": ["tofu", "seitan", "tempeh", "jackfruit", "chickpeas"],
        "beef": ["lentils", "mushrooms", "tempeh", "seitan", "plant-based beef"],
        "pork": ["jackfruit", "tempeh", "seitan", "tofu", "plant-based pork"],
        "fish": ["tofu", "tempeh", "hearts of palm", "banana blossom", "jackfruit"],
        "shrimp": ["king oyster mushroom", "tofu", "hearts of palm", "chickpeas"],
        "bacon": ["tempeh bacon", "coconut bacon", "rice paper bacon", "mushroom bacon"],
        "gelatin": ["agar-agar", "carrageenan", "pectin", "vegetable gum"]
    },
    "vegan": {
        "egg": ["flax egg", "chia egg", "applesauce", "banana", "silken tofu"],
        "milk": ["almond milk", "soy milk", "oat milk", "coconut milk", "rice milk"],
        "butter": ["coconut oil", "olive oil", "vegan butter", "applesauce", "avocado"],
        "cheese": ["nutritional yeast", "cashew cheese", "tofu", "vegan cheese"],
        "cream": ["coconut cream", "cashew cream", "silken tofu", "oat cream"],
        "yogurt": ["coconut yogurt", "soy yogurt", "almond yogurt", "cashew yogurt"],
        "honey": ["maple syrup", "agave nectar", "date syrup", "rice syrup"]
    },
    "gluten-free": {
        "flour": ["almond flour", "rice flour", "coconut flour", "gluten-free flour blend"],
        "pasta": ["rice pasta", "chickpea pasta", "corn pasta", "zucchini noodles"],
        "bread": ["gluten-free bread", "rice bread", "corn bread", "almond flour bread"],
        "breadcrumbs": ["gluten-free breadcrumbs", "cornmeal", "crushed rice crackers"],
        "soy sauce": ["tamari", "coconut aminos", "liquid aminos"],
        "couscous": ["quinoa", "millet", "rice", "buckwheat"]
    },
    "dairy-free": {
        "milk": ["almond milk", "soy milk", "oat milk", "coconut milk", "rice milk"],
        "butter": ["coconut oil", "olive oil", "vegan butter", "avocado"],
        "cheese": ["nutritional yeast", "cashew cheese", "vegan cheese"],
        "cream": ["coconut cream", "cashew cream", "oat cream"],
        "yogurt": ["coconut yogurt", "soy yogurt", "almond yogurt"],
        "ice cream": ["coconut ice cream", "cashew ice cream", "banana ice cream"]
    },
    "nut-free": {
        "peanut butter": ["sunflower seed butter", "pumpkin seed butter", "tahini"],
        "almond milk": ["oat milk", "rice milk", "hemp milk", "coconut milk"],
        "cashews": ["sunflower seeds", "pumpkin seeds", "hemp seeds"],
        "almonds": ["sunflower seeds", "pumpkin seeds", "hemp seeds", "watermelon seeds"],
        "walnuts": ["sunflower seeds", "pumpkin seeds", "hemp seeds"]
    }
}

class SubstitutionDatabase:
    """
    A class to manage ingredient substitutions.
    """
    
    def __init__(self, load_from_file: bool = True, use_llm: bool = USE_LLM):
        """
        Initialize the substitution database.
        
        Args:
            load_from_file: Whether to load existing database from file
            use_llm: Whether to use LLM for expanding substitutions
        """
        self.substitutions = {}
        self.use_llm = use_llm
        
        # Initialize with base substitutions
        self.substitutions = BASE_SUBSTITUTIONS.copy()
        
        # Load from file if it exists and is requested
        if load_from_file and os.path.exists(SUBSTITUTION_DB_PATH):
            self.load_from_file()
        
        # Expand using LLM if enabled
        if use_llm:
            self.expand_with_llm()
    
    def load_from_file(self) -> None:
        """Load substitution database from file."""
        try:
            with open(SUBSTITUTION_DB_PATH, 'r') as f:
                loaded_data = json.load(f)
                # Merge with existing data, preserving base substitutions
                for category, substitutions in loaded_data.items():
                    if category in self.substitutions:
                        # Update existing category with new substitutions
                        for ingredient, replacements in substitutions.items():
                            if ingredient in self.substitutions[category]:
                                # Merge lists, remove duplicates, and preserve order
                                combined = self.substitutions[category][ingredient] + [
                                    r for r in replacements 
                                    if r not in self.substitutions[category][ingredient]
                                ]
                                self.substitutions[category][ingredient] = combined
                            else:
                                self.substitutions[category][ingredient] = replacements
                    else:
                        # Add new category
                        self.substitutions[category] = substitutions
            print(f"Loaded substitution database from {SUBSTITUTION_DB_PATH}")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading substitution database: {e}")
    
    def save_to_file(self) -> None:
        """Save substitution database to file."""
        os.makedirs(os.path.dirname(SUBSTITUTION_DB_PATH), exist_ok=True)
        with open(SUBSTITUTION_DB_PATH, 'w') as f:
            json.dump(self.substitutions, f, indent=2)
        print(f"Saved substitution database to {SUBSTITUTION_DB_PATH}")
    
    def expand_with_llm(self) -> None:
        """Use LLM to expand substitution database with more mappings."""
        if not self.use_llm:
            return
            
        # This is where we would integrate with the LLM to generate more substitutions
        # For now, this is a placeholder. In a real implementation, we would:
        # 1. Load the LLM model specified in config
        # 2. For each category and ingredient, prompt the LLM for additional substitutions
        # 3. Add the generated substitutions to our database
        
        try:
            # Placeholder for LLM integration
            # In a real implementation, this would use llama-cpp-python or similar
            print("LLM integration is currently a placeholder.")
            print("In a real implementation, this would use Llama 3.1 to generate substitutions.")
            
            # Placeholder for demonstration purposes only
            # This would be generated by the LLM in a real implementation
            additional_substitutions = {
                "vegetarian": {
                    "anchovies": ["capers", "kalamata olives", "miso paste", "seaweed"],
                    "chicken broth": ["vegetable broth", "mushroom broth", "miso broth"],
                },
                "gluten-free": {
                    "beer": ["gluten-free beer", "wine", "cider"],
                    "oats": ["certified gluten-free oats", "quinoa flakes"],
                }
            }
            
            # Merge the additional substitutions
            for category, substitutions in additional_substitutions.items():
                if category in self.substitutions:
                    for ingredient, replacements in substitutions.items():
                        if ingredient in self.substitutions[category]:
                            # Combine and remove duplicates
                            current = self.substitutions[category][ingredient]
                            self.substitutions[category][ingredient] = current + [
                                r for r in replacements if r not in current
                            ]
                        else:
                            self.substitutions[category][ingredient] = replacements
                else:
                    self.substitutions[category] = substitutions
            
        except Exception as e:
            print(f"Error expanding substitutions with LLM: {e}")
    
    def get_substitutions(self, ingredient: str, category: str) -> List[str]:
        """
        Get substitutions for an ingredient in a specific category.
        
        Args:
            ingredient: The ingredient to find substitutions for
            category: The dietary restriction category
            
        Returns:
            List of substitution ingredients
        """
        # Normalize ingredient for case-insensitive matching
        ingredient = ingredient.lower().strip()
        
        # Check if category exists
        if category not in self.substitutions:
            return []
        
        # Check if ingredient has substitutions in this category
        # First try exact match
        if ingredient in self.substitutions[category]:
            return self.substitutions[category][ingredient]
        
        # Try partial match (e.g., "chicken breast" should match "chicken")
        for key in self.substitutions[category]:
            if key in ingredient or ingredient in key:
                return self.substitutions[category][key]
        
        return []
    
    def add_substitution(self, ingredient: str, substitutes: List[str], category: str) -> None:
        """
        Add a new substitution to the database.
        
        Args:
            ingredient: The ingredient to be substituted
            substitutes: List of possible substitutions
            category: The dietary restriction category
        """
        # Normalize ingredient
        ingredient = ingredient.lower().strip()
        
        # Ensure category exists
        if category not in self.substitutions:
            self.substitutions[category] = {}
        
        # Add or update substitution
        if ingredient in self.substitutions[category]:
            # Add new substitutes that aren't already in the list
            current = self.substitutions[category][ingredient]
            self.substitutions[category][ingredient] = current + [
                s for s in substitutes if s not in current
            ]
        else:
            self.substitutions[category][ingredient] = substitutes
        
        # Save changes to file
        self.save_to_file()


# Function to create a demonstration substitution database file
def create_demo_substitution_db():
    """Create a demonstration substitution database file with example data."""
    db = SubstitutionDatabase(load_from_file=False, use_llm=False)
    db.save_to_file()
    print(f"Created demonstration substitution database at {SUBSTITUTION_DB_PATH}")


if __name__ == "__main__":
    # When run as a script, create the demo database
    create_demo_substitution_db() 