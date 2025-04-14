"""
Recipe dataset module for the Recipe Substitution Search System.
This module provides functionality to load, process, and manage recipe collections.
"""

import json
import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Iterator

import pandas as pd

# Import local modules
from src.data.recipe import Recipe
from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Constants
PROCESSED_DATASET_PATH = PROCESSED_DATA_DIR / "processed_recipes.json"
ANNOTATIONS_PATH = PROCESSED_DATA_DIR / "annotations.json"


class RecipeDataset:
    """
    Class for managing a collection of recipes.
    """
    
    def __init__(self, load_from_processed: bool = True):
        """
        Initialize the recipe dataset.
        
        Args:
            load_from_processed: Whether to load the processed dataset
        """
        self.recipes: Dict[str, Recipe] = {}
        self.annotations: Dict[str, Dict[str, int]] = {}  # {query: {recipe_id: score}}
        
        # If requested, load processed dataset
        if load_from_processed and os.path.exists(PROCESSED_DATASET_PATH):
            self.load_processed_dataset()
            
        # Load annotations if available
        if os.path.exists(ANNOTATIONS_PATH):
            self.load_annotations()
    
    def load_raw_recipes(self, directory: Optional[Union[str, Path]] = None) -> None:
        """
        Load raw recipe data from files.
        
        Args:
            directory: Directory containing raw recipe files (defaults to RAW_DATA_DIR)
        """
        if directory is None:
            directory = RAW_DATA_DIR
        
        directory = Path(directory)
        
        # Ensure directory exists
        if not os.path.exists(directory):
            print(f"Raw data directory {directory} does not exist.")
            return
        
        # Find all JSON files in the directory
        json_files = glob.glob(str(directory / "*.json"))
        
        if not json_files:
            print(f"No JSON files found in {directory}.")
            return
        
        # Load recipes from each file
        recipe_count = 0
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    file_data = json.load(f)
                
                # Handle different file formats
                if isinstance(file_data, list):
                    # File contains a list of recipes
                    for recipe_data in file_data:
                        self._add_recipe_from_dict(recipe_data)
                        recipe_count += 1
                elif isinstance(file_data, dict):
                    if "recipes" in file_data:
                        # File contains a dict with a recipes list
                        for recipe_data in file_data["recipes"]:
                            self._add_recipe_from_dict(recipe_data)
                            recipe_count += 1
                    else:
                        # File contains a single recipe
                        self._add_recipe_from_dict(file_data)
                        recipe_count += 1
                        
            except Exception as e:
                print(f"Error loading recipes from {file_path}: {e}")
        
        print(f"Loaded {recipe_count} recipes from {len(json_files)} files in {directory}")
    
    def _add_recipe_from_dict(self, recipe_data: Dict) -> None:
        """
        Add a recipe from a dictionary to the dataset.
        
        Args:
            recipe_data: Dictionary containing recipe data
        """
        try:
            # Ensure recipe has an ID
            if "id" not in recipe_data:
                # Generate a simple ID based on title
                title = recipe_data.get("title", "").strip()
                if title:
                    recipe_data["id"] = re.sub(r'[^a-zA-Z0-9]', '_', title).lower()
                else:
                    # Skip recipes without title
                    return
            
            # Create Recipe object and add to collection
            recipe = Recipe.from_dict(recipe_data)
            self.recipes[recipe.id] = recipe
            
        except (ValueError, KeyError) as e:
            # Skip invalid recipes
            pass
    
    def load_processed_dataset(self) -> None:
        """Load processed dataset from file."""
        try:
            with open(PROCESSED_DATASET_PATH, 'r') as f:
                recipes_data = json.load(f)
            
            self.recipes = {}
            for recipe_dict in recipes_data:
                try:
                    recipe = Recipe.from_dict(recipe_dict)
                    self.recipes[recipe.id] = recipe
                except (ValueError, KeyError):
                    # Skip invalid recipes
                    continue
            
            print(f"Loaded {len(self.recipes)} recipes from {PROCESSED_DATASET_PATH}")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading processed dataset: {e}")
    
    def save_processed_dataset(self) -> None:
        """Save processed dataset to file."""
        os.makedirs(os.path.dirname(PROCESSED_DATASET_PATH), exist_ok=True)
        
        # Convert recipes to list of dictionaries
        recipes_data = [recipe.to_dict() for recipe in self.recipes.values()]
        
        with open(PROCESSED_DATASET_PATH, 'w') as f:
            json.dump(recipes_data, f, indent=2)
        
        print(f"Saved {len(recipes_data)} recipes to {PROCESSED_DATASET_PATH}")
    
    def load_annotations(self) -> None:
        """Load recipe annotations from file."""
        try:
            with open(ANNOTATIONS_PATH, 'r') as f:
                self.annotations = json.load(f)
            
            print(f"Loaded annotations for {len(self.annotations)} queries from {ANNOTATIONS_PATH}")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading annotations: {e}")
    
    def save_annotations(self) -> None:
        """Save recipe annotations to file."""
        os.makedirs(os.path.dirname(ANNOTATIONS_PATH), exist_ok=True)
        
        with open(ANNOTATIONS_PATH, 'w') as f:
            json.dump(self.annotations, f, indent=2)
        
        print(f"Saved annotations for {len(self.annotations)} queries to {ANNOTATIONS_PATH}")
    
    def add_annotation(self, query: str, recipe_id: str, score: int) -> None:
        """
        Add a relevance annotation for a recipe.
        
        Args:
            query: Search query
            recipe_id: ID of the recipe
            score: Relevance score (0-2)
        """
        if recipe_id not in self.recipes:
            print(f"Recipe {recipe_id} not found in dataset. Annotation not added.")
            return
        
        if score not in (0, 1, 2):
            print(f"Invalid score {score}. Must be 0, 1, or 2. Annotation not added.")
            return
        
        # Ensure query exists in annotations
        if query not in self.annotations:
            self.annotations[query] = {}
        
        # Add or update annotation
        self.annotations[query][recipe_id] = score
        
        # Save annotations to file
        self.save_annotations()
    
    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """
        Get a recipe by ID.
        
        Args:
            recipe_id: ID of the recipe
            
        Returns:
            Recipe object or None if not found
        """
        return self.recipes.get(recipe_id)
    
    def get_all_recipes(self) -> List[Recipe]:
        """
        Get all recipes in the dataset.
        
        Returns:
            List of Recipe objects
        """
        return list(self.recipes.values())
    
    def search_by_title(self, query: str) -> List[Recipe]:
        """
        Search recipes by title.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Recipe objects
        """
        query_terms = query.lower().split()
        results = []
        
        for recipe in self.recipes.values():
            title_lower = recipe.title.lower()
            # Check if all query terms are in the title
            if all(term in title_lower for term in query_terms):
                results.append(recipe)
        
        return results
    
    def search_by_ingredient(self, ingredient: str) -> List[Recipe]:
        """
        Search recipes containing a specific ingredient.
        
        Args:
            ingredient: Ingredient to search for
            
        Returns:
            List of matching Recipe objects
        """
        return [recipe for recipe in self.recipes.values() if recipe.has_ingredient(ingredient)]
    
    def search_by_category(self, category: str) -> List[Recipe]:
        """
        Search recipes by substitution category.
        
        Args:
            category: Substitution category to search for
            
        Returns:
            List of matching Recipe objects
        """
        return [recipe for recipe in self.recipes.values() if recipe.has_substitution_category(category)]
    
    def get_annotations_for_query(self, query: str) -> Dict[str, int]:
        """
        Get annotations for a specific query.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary mapping recipe IDs to scores
        """
        return self.annotations.get(query, {})
    
    def get_annotation_stats(self) -> Dict:
        """
        Get statistics about the annotations.
        
        Returns:
            Dictionary with annotation statistics
        """
        total_annotations = sum(len(annotations) for annotations in self.annotations.values())
        queries_count = len(self.annotations)
        
        # Count annotations by score
        score_counts = {0: 0, 1: 0, 2: 0}
        for query_annotations in self.annotations.values():
            for score in query_annotations.values():
                score_counts[score] += 1
        
        return {
            "total_annotations": total_annotations,
            "queries_count": queries_count,
            "annotations_by_score": score_counts
        }
    
    def __len__(self) -> int:
        """Return the number of recipes in the dataset."""
        return len(self.recipes)
    
    def __iter__(self) -> Iterator[Recipe]:
        """Iterate over recipes in the dataset."""
        return iter(self.recipes.values())


# Demo data generation
def create_demo_recipes():
    """Create a demonstration dataset with example recipes."""
    # Placeholder function to create some demo recipes
    recipes = [
        {
            "id": "pad_thai_original",
            "title": "Classic Pad Thai",
            "ingredients": [
                "8 oz rice noodles",
                "2 tbsp vegetable oil",
                "2 eggs, beaten",
                "1 lb shrimp, peeled and deveined",
                "2 cloves garlic, minced",
                "1 shallot, thinly sliced",
                "1/4 cup tamarind paste",
                "3 tbsp fish sauce",
                "2 tbsp palm sugar",
                "1/2 tsp red chili flakes",
                "2 cups bean sprouts",
                "4 green onions, sliced",
                "1/4 cup roasted peanuts, chopped",
                "Lime wedges for serving",
                "Fresh cilantro for garnish"
            ],
            "instructions": "Soak rice noodles in warm water until softened. Heat oil in a wok and scramble eggs. Add shrimp, garlic, and shallot. Stir in noodles and sauce ingredients. Cook until noodles are tender. Toss with bean sprouts and green onions. Serve garnished with peanuts, cilantro, and lime wedges.",
            "cuisine": "Thai",
            "tags": ["asian", "dinner", "seafood", "noodles"]
        },
        {
            "id": "pad_thai_vegetarian",
            "title": "Vegetarian Pad Thai with Tofu",
            "ingredients": [
                "8 oz rice noodles",
                "2 tbsp vegetable oil",
                "14 oz firm tofu, pressed and cubed",
                "2 eggs, beaten (optional, omit for vegan)",
                "2 cloves garlic, minced",
                "1 shallot, thinly sliced",
                "1/4 cup tamarind paste",
                "3 tbsp soy sauce",
                "2 tbsp palm sugar or brown sugar",
                "1/2 tsp red chili flakes",
                "2 cups bean sprouts",
                "4 green onions, sliced",
                "1/4 cup roasted peanuts, chopped",
                "Lime wedges for serving",
                "Fresh cilantro for garnish"
            ],
            "instructions": "Soak rice noodles in warm water until softened. Heat oil in a wok and cook tofu until golden. If using eggs, push tofu aside and scramble eggs. Add garlic and shallot. Stir in noodles and sauce ingredients. Cook until noodles are tender. Toss with bean sprouts and green onions. Serve garnished with peanuts, cilantro, and lime wedges.",
            "cuisine": "Thai",
            "diet_labels": ["vegetarian"],
            "tags": ["asian", "dinner", "vegetarian", "noodles", "tofu"]
        },
        {
            "id": "pancakes_original",
            "title": "Classic Fluffy Pancakes",
            "ingredients": [
                "1 1/2 cups all-purpose flour",
                "3 1/2 tsp baking powder",
                "1 tsp salt",
                "1 tbsp white sugar",
                "1 1/4 cups milk",
                "1 egg",
                "3 tbsp butter, melted",
                "1 tsp vanilla extract"
            ],
            "instructions": "In a large bowl, sift together flour, baking powder, salt, and sugar. Make a well in the center and pour in milk, egg, melted butter, and vanilla. Mix until smooth. Heat a lightly oiled griddle or frying pan over medium-high heat. Pour batter onto the griddle, using approximately 1/4 cup for each pancake. Brown on both sides and serve hot with maple syrup.",
            "tags": ["breakfast", "american", "quick"]
        },
        {
            "id": "pancakes_gluten_free",
            "title": "Gluten-Free Oat Flour Pancakes",
            "ingredients": [
                "1 1/2 cups oat flour (certified gluten-free)",
                "2 tsp baking powder",
                "1/2 tsp baking soda",
                "1 tsp salt",
                "1 tbsp white sugar",
                "1 1/4 cups almond milk",
                "1 egg",
                "3 tbsp coconut oil, melted",
                "1 tsp vanilla extract",
                "1/2 tsp xanthan gum (optional, for better texture)"
            ],
            "instructions": "In a large bowl, whisk together oat flour, baking powder, baking soda, salt, and sugar. In another bowl, beat egg and mix with almond milk, melted coconut oil, and vanilla. Add wet ingredients to dry ingredients and mix until just combined. Let batter rest for 5 minutes. Heat a lightly oiled griddle over medium heat. Pour batter onto the griddle, using approximately 1/4 cup for each pancake. Cook until bubbles form, then flip and cook until browned. Serve with maple syrup.",
            "diet_labels": ["gluten-free"],
            "tags": ["breakfast", "american", "quick", "gluten-free"]
        }
    ]
    
    # Create dataset and add recipes
    dataset = RecipeDataset(load_from_processed=False)
    for recipe_data in recipes:
        dataset._add_recipe_from_dict(recipe_data)
    
    # Add some annotations
    dataset.add_annotation("vegetarian pad thai", "pad_thai_vegetarian", 2)
    dataset.add_annotation("vegetarian pad thai", "pad_thai_original", 0)
    dataset.add_annotation("gluten-free pancakes", "pancakes_gluten_free", 1)
    dataset.add_annotation("gluten-free pancakes", "pancakes_original", 0)
    
    # Save the processed dataset
    dataset.save_processed_dataset()
    
    print(f"Created demonstration dataset with {len(dataset)} recipes and annotations for 2 queries.")


if __name__ == "__main__":
    # When run as a script, create the demo dataset
    create_demo_recipes() 