"""
Main script for the Recipe Substitution Search System.
This script provides a command-line interface for searching recipes.
"""

import argparse
import os
import sys
import textwrap
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from src.data.recipe import Recipe
from src.data.recipe_dataset import RecipeDataset, create_demo_recipes
from src.data.substitution_db import SubstitutionDatabase, create_demo_substitution_db
from src.models.search_engine import RecipeSearchEngine, SubstitutionSearchEngine
from src.utils.config import PROCESSED_DATA_DIR


def initialize_system(use_enhanced_engine: bool = True) -> Tuple[RecipeDataset, RecipeSearchEngine]:
    """
    Initialize the recipe dataset and search engine.
    
    Args:
        use_enhanced_engine: Whether to use the enhanced substitution search engine
        
    Returns:
        Tuple of (dataset, search_engine)
    """
    # Check if processed data exists, if not create demo data
    if not os.path.exists(PROCESSED_DATA_DIR / "processed_recipes.json"):
        print("No processed recipe data found. Creating demo data...")
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
        create_demo_recipes()
        create_demo_substitution_db()
    
    # Load dataset and substitution database
    dataset = RecipeDataset(load_from_processed=True)
    substitution_db = SubstitutionDatabase()
    
    # Create appropriate search engine
    if use_enhanced_engine:
        search_engine = SubstitutionSearchEngine(dataset, substitution_db)
    else:
        search_engine = RecipeSearchEngine(dataset, substitution_db)
    
    return dataset, search_engine


def print_recipe(recipe: Recipe, score: Optional[float] = None, 
               annotation: Optional[int] = None, max_ingredients: int = 5,
               show_details: bool = False):
    """
    Print a recipe in a formatted way.
    
    Args:
        recipe: Recipe to print
        score: Search score (if available)
        annotation: Annotation score (if available)
        max_ingredients: Maximum number of ingredients to show
        show_details: Whether to show full recipe details
    """
    # Title with score information
    title_line = f"📗 {recipe.title}"
    if score is not None:
        title_line += f" (Score: {score:.2f})"
    if annotation is not None:
        title_line += f" [Annotation: {annotation}]"
    
    print("\n" + "=" * 80)
    print(title_line)
    print("=" * 80)
    
    # Diet labels and tags
    if recipe.diet_labels:
        print(f"📋 Diet: {', '.join(recipe.diet_labels)}")
    if recipe.tags:
        print(f"🏷️ Tags: {', '.join(recipe.tags)}")
    
    # URL
    if recipe.url:
        print(f"🔗 URL: {recipe.url}")
    
    # Ingredients (truncated if many)
    print("\n🥕 Ingredients:")
    if show_details or len(recipe.ingredients) <= max_ingredients:
        for ingredient in recipe.ingredients:
            print(f"  • {ingredient}")
    else:
        for ingredient in recipe.ingredients[:max_ingredients]:
            print(f"  • {ingredient}")
        print(f"  • ... and {len(recipe.ingredients) - max_ingredients} more ingredients")
    
    # Instructions (truncated unless show_details is True)
    if recipe.instructions:
        print("\n📝 Instructions:")
        if show_details:
            # Print full instructions with wrapping
            wrapped_instructions = textwrap.fill(
                recipe.instructions, width=76, initial_indent="  ", subsequent_indent="  "
            )
            print(wrapped_instructions)
        else:
            # Print just the first 200 characters
            short_instructions = recipe.instructions[:200]
            if len(recipe.instructions) > 200:
                short_instructions += "..."
            
            wrapped_instructions = textwrap.fill(
                short_instructions, width=76, initial_indent="  ", subsequent_indent="  "
            )
            print(wrapped_instructions)
    
    # Additional details if requested
    if show_details:
        if recipe.cooking_time:
            print(f"\n⏱️ Cooking Time: {recipe.cooking_time} minutes")
        if recipe.serving_size:
            print(f"🍽️ Servings: {recipe.serving_size}")
        if recipe.nutrition:
            print("\n📊 Nutrition Information:")
            for key, value in recipe.nutrition.items():
                print(f"  • {key}: {value}")
    
    print()


def search_recipes(query: str, dataset: RecipeDataset, search_engine: RecipeSearchEngine, 
                 top_k: int = 5, show_details: bool = False):
    """
    Search for recipes and display results.
    
    Args:
        query: Search query
        dataset: Recipe dataset
        search_engine: Search engine to use
        top_k: Number of results to display
        show_details: Whether to show full recipe details
    """
    print(f"\nSearching for: {query}")
    print("-" * 80)
    
    # Perform search
    results = search_engine.search(query, top_k=top_k)
    
    if not results:
        print("No results found. Try a different query.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    # Get annotations if available
    for i, (recipe, score) in enumerate(results):
        # Get annotation if available
        annotation = search_engine.get_annotation_for_result(query, recipe)
        
        # Print recipe
        print(f"Result #{i+1}:")
        print_recipe(recipe, score, annotation, show_details=show_details)


def list_available_queries(dataset: RecipeDataset):
    """
    List queries that have annotations.
    
    Args:
        dataset: Recipe dataset
    """
    print("\nAvailable annotated queries:")
    print("-" * 80)
    
    if not dataset.annotations:
        print("No annotated queries available.")
        return
    
    for i, query in enumerate(dataset.annotations.keys()):
        annotation_count = len(dataset.annotations[query])
        print(f"{i+1}. {query} ({annotation_count} annotations)")


def interactive_mode(dataset: RecipeDataset, search_engine: RecipeSearchEngine):
    """
    Run the search system in interactive mode.
    
    Args:
        dataset: Recipe dataset
        search_engine: Search engine to use
    """
    print("\nRecipe Substitution Search System - Interactive Mode")
    print("=" * 80)
    print("Enter a search query (e.g., 'vegetarian pad thai') or a command:")
    print("  help    - Show this help")
    print("  queries - List available annotated queries")
    print("  stats   - Show dataset statistics")
    print("  exit    - Exit the program")
    print("=" * 80)
    
    while True:
        try:
            user_input = input("\nEnter query or command: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == "exit":
                print("Exiting. Goodbye!")
                break
                
            elif user_input.lower() == "help":
                print("\nCommands:")
                print("  help    - Show this help")
                print("  queries - List available annotated queries")
                print("  stats   - Show dataset statistics")
                print("  exit    - Exit the program")
                print("\nOr enter a search query like 'vegetarian pad thai'")
                
            elif user_input.lower() == "queries":
                list_available_queries(dataset)
                
            elif user_input.lower() == "stats":
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
                
            else:
                # Treat as search query
                search_recipes(user_input, dataset, search_engine, top_k=5, show_details=True)
                
        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
            
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Recipe Substitution Search System")
    
    # Command line arguments
    parser.add_argument("action", nargs="?", choices=["search", "interactive"], 
                      default="interactive", help="Action to perform")
    parser.add_argument("query", nargs="?", help="Search query (required for search action)")
    parser.add_argument("--basic", action="store_true", help="Use basic search engine instead of enhanced")
    parser.add_argument("--results", type=int, default=5, help="Number of results to display")
    parser.add_argument("--details", action="store_true", help="Show full recipe details")
    
    args = parser.parse_args()
    
    # Initialize system
    dataset, search_engine = initialize_system(use_enhanced_engine=not args.basic)
    
    # Perform requested action
    if args.action == "search":
        if not args.query:
            print("Error: Query is required for search action.")
            parser.print_help()
            return 1
            
        search_recipes(args.query, dataset, search_engine, 
                     top_k=args.results, show_details=args.details)
        return 0
        
    elif args.action == "interactive":
        interactive_mode(dataset, search_engine)
        return 0


if __name__ == "__main__":
    sys.exit(main()) 