"""
Initialization script for the Recipe Substitution Search System.
This script sets up the system with demo data for testing.
"""

import argparse
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.recipe_dataset import create_demo_recipes
from src.data.substitution_db import create_demo_substitution_db
from scripts.data_collector import create_dummy_recipes
from src.utils.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def initialize_system(recipe_count: int = 50, force_reset: bool = False):
    """
    Initialize the Recipe Substitution Search System with demo data.
    
    Args:
        recipe_count: Number of dummy recipes to create
        force_reset: Whether to force reset the system (delete existing data)
    """
    print("Initializing Recipe Substitution Search System...")
    
    # Create directories if they don't exist
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # Check if data already exists
    processed_data_exists = os.path.exists(os.path.join(PROCESSED_DATA_DIR, "processed_recipes.json"))
    
    if processed_data_exists and not force_reset:
        print("Data already exists. Use --force to reset the system.")
        return
    
    if force_reset:
        print("Forcing reset of the system...")
        # Delete existing processed data files
        for filename in os.listdir(PROCESSED_DATA_DIR):
            file_path = os.path.join(PROCESSED_DATA_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"Deleted {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
    
    # Create demo data
    print("\nCreating base demo recipes...")
    create_demo_recipes()
    
    print("\nCreating demo substitution database...")
    create_demo_substitution_db()
    
    print("\nCreating additional dummy recipes for testing...")
    create_dummy_recipes(recipe_count)
    
    print("\nSystem initialization complete!")
    print("\nYou can now use the system with the following commands:")
    print("  python src/main.py - Launch interactive search mode")
    print("  python src/main.py search 'vegetarian pad thai' - Search for a specific query")
    print("  python src/evaluation/run_evaluation.py - Run system evaluation")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Initialize Recipe Substitution Search System")
    
    parser.add_argument("--count", type=int, default=50, 
                      help="Number of dummy recipes to create")
    parser.add_argument("--force", action="store_true", 
                      help="Force reset of the system (delete existing data)")
    
    args = parser.parse_args()
    
    initialize_system(recipe_count=args.count, force_reset=args.force)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 