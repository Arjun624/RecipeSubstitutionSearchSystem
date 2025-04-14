"""
Data collection script for the Recipe Substitution Search System.
This script provides utilities for collecting recipe data and managing annotations.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
import random

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.recipe import Recipe
from src.data.recipe_dataset import RecipeDataset
from src.models.search_engine import RecipeSearchEngine, SubstitutionSearchEngine
from src.data.substitution_db import SubstitutionDatabase
from src.utils.config import RAW_DATA_DIR, SUBSTITUTION_CATEGORIES

# Try to import requests, beautifulsoup for web scraping
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("Warning: requests and/or beautifulsoup4 not installed. Web scraping will be disabled.")
    print("To enable, install with: pip install requests beautifulsoup4")


def collect_recipes_from_web(search_term: str, limit: int = 10) -> List[Dict]:
    """
    Collect recipes from web search results.
    This is a placeholder implementation - in a real system,
    you would use a more sophisticated approach with proper API keys.
    
    Args:
        search_term: Term to search for
        limit: Maximum number of recipes to collect
        
    Returns:
        List of recipe dictionaries
    """
    if not WEB_SCRAPING_AVAILABLE:
        print("Web scraping is not available. Please install required packages.")
        return []
    
    print(f"Searching for recipes matching: {search_term}")
    
    # This is a placeholder - in a real implementation, you would:
    # 1. Use a proper recipe API (like Spoonacular, Edamam, etc.)
    # 2. Or implement proper web scraping for specific recipe sites
    # 3. Handle pagination, rate limiting, etc.
    
    # Placeholder implementation - generates fake data
    recipes = []
    
    for i in range(min(5, limit)):  # Pretend we found some recipes
        recipe_id = f"web_{search_term.replace(' ', '_')}_{i}"
        
        recipe = {
            "id": recipe_id,
            "title": f"{search_term.title()} Recipe {i+1}",
            "ingredients": [
                "Ingredient 1",
                "Ingredient 2",
                "Ingredient 3",
                f"{search_term} specific ingredient",
                "Common ingredient"
            ],
            "instructions": f"Instructions for making {search_term}. This is a placeholder.",
            "url": f"https://example.com/recipes/{recipe_id}",
            "tags": [tag for tag in search_term.split()],
        }
        
        # Add diet labels if search term contains dietary terms
        for category in SUBSTITUTION_CATEGORIES:
            if category in search_term.lower():
                recipe["diet_labels"] = [category]
                break
        
        recipes.append(recipe)
    
    print(f"Found {len(recipes)} recipes matching '{search_term}'")
    return recipes


def save_recipes_to_file(recipes: List[Dict], filename: str = None) -> str:
    """
    Save recipes to a JSON file.
    
    Args:
        recipes: List of recipe dictionaries
        filename: Name of file to save to (if None, generate a name)
        
    Returns:
        Path to the saved file
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    if filename is None:
        # Generate a filename based on current time
        timestamp = int(time.time())
        filename = f"recipes_{timestamp}.json"
    
    file_path = os.path.join(RAW_DATA_DIR, filename)
    
    with open(file_path, 'w') as f:
        json.dump(recipes, f, indent=2)
    
    print(f"Saved {len(recipes)} recipes to {file_path}")
    return file_path


def annotate_search_results(query: str, dataset: RecipeDataset, search_engine: RecipeSearchEngine):
    """
    Interactive tool for annotating search results.
    
    Args:
        query: Search query
        dataset: Recipe dataset
        search_engine: Search engine to use
    """
    print(f"\nAnnotating search results for query: {query}")
    print("=" * 80)
    print("For each result, enter a relevance score (0-2):")
    print("  0 - Recipe misses the mark (doesn't achieve substitution or loses dish essence)")
    print("  1 - Okay match (makes substitution but loses something in translation)")
    print("  2 - Great match (successfully implements substitution and maintains dish essence)")
    print("Or enter one of these commands:")
    print("  s - Skip this recipe")
    print("  q - Quit annotation mode")
    print("=" * 80)
    
    # Perform search
    results = search_engine.search(query, top_k=20)  # Get more results to annotate
    
    if not results:
        print("No results found for this query.")
        return
    
    # Get existing annotations
    existing_annotations = dataset.get_annotations_for_query(query)
    
    # Track new annotations
    annotations_added = 0
    
    for i, (recipe, score) in enumerate(results):
        # Skip if already annotated
        if recipe.id in existing_annotations:
            print(f"\nRecipe already annotated: {recipe.title}")
            print(f"Current annotation: {existing_annotations[recipe.id]}")
            
            override = input("Override annotation? (y/n) [n]: ").strip().lower()
            if override != 'y':
                continue
        
        # Display recipe
        print(f"\nResult #{i+1}:")
        from src.main import print_recipe  # Import here to avoid circular imports
        print_recipe(recipe, score, show_details=True)
        
        # Get annotation
        while True:
            annotation = input("Enter score (0-2) or command: ").strip().lower()
            
            if annotation == 'q':
                print("Quitting annotation mode.")
                return
            
            if annotation == 's':
                print("Skipping this recipe.")
                break
            
            try:
                score = int(annotation)
                if score not in (0, 1, 2):
                    print("Invalid score. Must be 0, 1, or 2.")
                    continue
                
                # Add annotation
                dataset.add_annotation(query, recipe.id, score)
                annotations_added += 1
                print(f"Added annotation: {recipe.title} = {score}")
                break
                
            except ValueError:
                print("Invalid input. Enter a score (0-2) or command (s/q).")
    
    print(f"\nAnnotation complete. Added {annotations_added} annotations for query '{query}'.")


def collect_data_interactive():
    """Interactive data collection session."""
    # Initialize system
    dataset = RecipeDataset(load_from_processed=True)
    substitution_db = SubstitutionDatabase()
    search_engine = SubstitutionSearchEngine(dataset, substitution_db)
    
    print("\nRecipe Substitution Search System - Data Collection Mode")
    print("=" * 80)
    print("Commands:")
    print("  collect <search term> - Collect recipes from web search")
    print("  annotate <query> - Annotate search results for a query")
    print("  stats - Show dataset statistics")
    print("  queries - List existing annotated queries")
    print("  exit - Exit data collection mode")
    print("=" * 80)
    
    while True:
        try:
            command = input("\nEnter command: ").strip()
            
            if not command:
                continue
                
            if command.lower() == "exit":
                print("Exiting data collection mode.")
                break
                
            elif command.lower() == "stats":
                recipe_count = len(dataset)
                query_count = len(dataset.annotations)
                annotation_count = sum(len(annotations) for annotations in dataset.annotations.values())
                
                print("\nDataset Statistics:")
                print(f"  Recipes: {recipe_count}")
                print(f"  Annotated Queries: {query_count}")
                print(f"  Total Annotations: {annotation_count}")
                
                if annotation_count > 0:
                    annotation_stats = dataset.get_annotation_stats()
                    print("\nAnnotation Distribution:")
                    for score, count in annotation_stats["annotations_by_score"].items():
                        print(f"  Score {score}: {count} annotations")
                
            elif command.lower() == "queries":
                # List existing annotated queries
                if not dataset.annotations:
                    print("No annotated queries available.")
                else:
                    print("\nExisting annotated queries:")
                    for i, query in enumerate(dataset.annotations.keys()):
                        annotation_count = len(dataset.annotations[query])
                        print(f"{i+1}. {query} ({annotation_count} annotations)")
            
            elif command.lower().startswith("collect "):
                search_term = command[8:].strip()
                if not search_term:
                    print("Please specify a search term.")
                    continue
                
                # Collect recipes from web
                recipes = collect_recipes_from_web(search_term)
                
                if recipes:
                    # Save to file
                    save_recipes_to_file(recipes)
                    
                    # Add to dataset
                    for recipe_data in recipes:
                        try:
                            recipe = Recipe.from_dict(recipe_data)
                            dataset.recipes[recipe.id] = recipe
                        except Exception as e:
                            print(f"Error adding recipe: {e}")
                    
                    # Save dataset
                    dataset.save_processed_dataset()
                    print(f"Added {len(recipes)} recipes to dataset.")
                else:
                    print("No recipes collected.")
            
            elif command.lower().startswith("annotate "):
                query = command[9:].strip()
                if not query:
                    print("Please specify a query to annotate.")
                    continue
                
                # Annotate search results
                annotate_search_results(query, dataset, search_engine)
                
            else:
                print("Unknown command. Type 'exit' to quit.")
                
        except KeyboardInterrupt:
            print("\nExiting data collection mode.")
            break
            
        except Exception as e:
            print(f"Error: {e}")


def create_dummy_recipes(count: int = 50):
    """
    Create dummy recipes for testing purposes.
    
    Args:
        count: Number of recipes to create
    """
    print(f"Creating {count} dummy recipes for testing...")
    
    # Load existing dataset if available
    dataset = RecipeDataset(load_from_processed=True)
    
    # Dish types to use for dummy recipes
    dish_types = [
        "pad thai", "pancakes", "chocolate chip cookies", "carbonara", 
        "mac and cheese", "alfredo sauce", "pesto", "brownies", 
        "lasagna", "banana bread", "pizza", "stir fry", "curry", 
        "soup", "salad", "burger", "sandwich", "cake", "pie", "muffins"
    ]
    
    # Substitution categories
    substitution_categories = SUBSTITUTION_CATEGORIES
    
    # Create dummy recipes
    recipes_created = 0
    
    for dish_type in dish_types:
        # Create original version
        recipe_id = f"dummy_{dish_type.replace(' ', '_')}_original"
        
        if recipe_id in dataset.recipes:
            continue  # Skip if already exists
            
        recipe_data = {
            "id": recipe_id,
            "title": f"Classic {dish_type.title()}",
            "ingredients": [
                f"Basic ingredient for {dish_type} 1",
                f"Basic ingredient for {dish_type} 2",
                f"Basic ingredient for {dish_type} 3",
                "Common ingredient 1",
                "Common ingredient 2"
            ],
            "instructions": f"Instructions for making classic {dish_type}. This is a dummy recipe.",
            "tags": [tag for tag in dish_type.split()] + ["classic", "original"]
        }
        
        dataset.recipes[recipe_id] = Recipe.from_dict(recipe_data)
        recipes_created += 1
        
        # Create substitution versions
        for category in substitution_categories:
            if recipes_created >= count:
                break
                
            recipe_id = f"dummy_{dish_type.replace(' ', '_')}_{category}"
            
            if recipe_id in dataset.recipes:
                continue  # Skip if already exists
                
            recipe_data = {
                "id": recipe_id,
                "title": f"{category.title()} {dish_type.title()}",
                "ingredients": [
                    f"{category} substitute for {dish_type} 1",
                    f"{category} substitute for {dish_type} 2",
                    f"Basic ingredient for {dish_type} 3",
                    "Common ingredient 1",
                    "Common ingredient 2"
                ],
                "instructions": f"Instructions for making {category} {dish_type}. This is a dummy recipe.",
                "diet_labels": [category],
                "tags": [tag for tag in dish_type.split()] + [category, "substitution"]
            }
            
            dataset.recipes[recipe_id] = Recipe.from_dict(recipe_data)
            recipes_created += 1
            
            # Add annotation
            # Randomly assign scores, but bias toward 1 and 2 for better testing
            scores = [0, 1, 1, 2, 2]
            score = random.choice(scores)
            
            query = f"{category} {dish_type}"
            dataset.add_annotation(query, recipe_id, score)
        
        if recipes_created >= count:
            break
    
    # Save dataset
    dataset.save_processed_dataset()
    print(f"Created {recipes_created} dummy recipes with annotations.")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Recipe Data Collection Tool")
    
    # Command line arguments
    parser.add_argument("action", choices=["collect", "annotate", "generate"], 
                      help="Action to perform")
    parser.add_argument("--query", type=str, help="Query for annotation or collection")
    parser.add_argument("--count", type=int, default=50, help="Number of dummy recipes to generate")
    
    args = parser.parse_args()
    
    if args.action == "collect":
        if not args.query:
            # Interactive mode
            collect_data_interactive()
        else:
            # Collect recipes for a specific term
            recipes = collect_recipes_from_web(args.query)
            if recipes:
                save_recipes_to_file(recipes)
    
    elif args.action == "annotate":
        if not args.query:
            print("Error: Query is required for annotation.")
            parser.print_help()
            return 1
            
        # Initialize system
        dataset = RecipeDataset(load_from_processed=True)
        substitution_db = SubstitutionDatabase()
        search_engine = SubstitutionSearchEngine(dataset, substitution_db)
        
        # Annotate search results
        annotate_search_results(args.query, dataset, search_engine)
    
    elif args.action == "generate":
        # Create dummy recipes
        create_dummy_recipes(args.count)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 