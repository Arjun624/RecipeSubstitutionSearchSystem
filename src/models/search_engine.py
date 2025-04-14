"""
Search engine module for the Recipe Substitution Search System.
This module provides the core search functionality for finding recipes
with successful substitutions.
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Union

from src.data.recipe import Recipe
from src.data.recipe_dataset import RecipeDataset
from src.data.substitution_db import SubstitutionDatabase
from src.utils.recipe_utils import normalize_ingredient, calculate_ingredient_overlap


class RecipeSearchEngine:
    """
    Search engine for finding recipes with successful substitutions.
    """
    
    def __init__(self, dataset: RecipeDataset, substitution_db: SubstitutionDatabase):
        """
        Initialize the search engine.
        
        Args:
            dataset: Recipe dataset
            substitution_db: Substitution database
        """
        self.dataset = dataset
        self.substitution_db = substitution_db
    
    def parse_query(self, query: str) -> Tuple[str, str]:
        """
        Parse a query to extract dish type and substitution category.
        
        Args:
            query: User query (e.g., "vegetarian pad thai")
            
        Returns:
            Tuple of (substitution_category, dish_type)
        """
        # List of known substitution categories
        categories = [
            "vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free",
            "egg-free", "sugar-free", "low-carb", "keto", "paleo",
            "whole30", "allergen-free"
        ]
        
        # Convert to lowercase for case-insensitive matching
        query_lower = query.lower()
        
        # Try to find a substitution category
        substitution_category = None
        dish_type = query_lower  # Default: the whole query is the dish type
        
        for category in categories:
            if category in query_lower:
                substitution_category = category
                # Remove the category from the query to get the dish type
                dish_type = query_lower.replace(category, "").strip()
                break
        
        return substitution_category, dish_type
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Recipe, float]]:
        """
        Search for recipes matching a query.
        
        Args:
            query: User search query (e.g., "vegetarian pad thai")
            top_k: Number of top results to return
            
        Returns:
            List of (recipe, score) tuples
        """
        # Parse query to extract substitution category and dish type
        substitution_category, dish_type = self.parse_query(query)
        
        # If no substitution category was found, just do a direct title search
        if not substitution_category:
            results = self.dataset.search_by_title(query)
            return [(recipe, 1.0) for recipe in results[:top_k]]
        
        # Step 1: Find recipes matching the dish type
        base_recipes = self.dataset.search_by_title(dish_type)
        
        # If no base recipes found, try a more lenient search
        if not base_recipes:
            # Split dish type into words and search for recipes containing any of them
            dish_words = dish_type.split()
            recipe_matches = {}
            
            for word in dish_words:
                if len(word) < 3:  # Skip very short words
                    continue
                    
                matches = self.dataset.search_by_title(word)
                for recipe in matches:
                    if recipe.id in recipe_matches:
                        recipe_matches[recipe.id] += 1
                    else:
                        recipe_matches[recipe.id] = 1
            
            # Get recipes with the most word matches
            if recipe_matches:
                sorted_matches = sorted(recipe_matches.items(), key=lambda x: x[1], reverse=True)
                base_recipes = [self.dataset.get_recipe(recipe_id) for recipe_id, _ in sorted_matches]
                base_recipes = [recipe for recipe in base_recipes if recipe]  # Filter out None values
        
        # Step 2: Find recipes matching the substitution category
        substitution_recipes = self.dataset.search_by_category(substitution_category)
        
        # If no base or substitution recipes found, return empty list
        if not base_recipes and not substitution_recipes:
            return []
        
        # Step 3: Rank the recipes
        ranked_recipes = self._rank_recipes(base_recipes, substitution_recipes, 
                                          substitution_category, dish_type)
        
        # Return top-k results
        return ranked_recipes[:top_k]
    
    def _rank_recipes(self, 
                    base_recipes: List[Recipe], 
                    substitution_recipes: List[Recipe],
                    substitution_category: str, 
                    dish_type: str) -> List[Tuple[Recipe, float]]:
        """
        Rank recipes based on relevance to the query.
        
        Args:
            base_recipes: List of recipes matching the dish type
            substitution_recipes: List of recipes matching the substitution category
            substitution_category: Substitution category from the query
            dish_type: Dish type from the query
            
        Returns:
            List of (recipe, score) tuples, sorted by score in descending order
        """
        # Dictionary to store recipe scores
        recipe_scores: Dict[str, float] = {}
        
        # If we have base recipes, use them as a reference for scoring
        if base_recipes:
            # Get the "most representative" base recipe
            # (simple heuristic: the one with the most ingredient overlap with other base recipes)
            representative_base = self._find_representative_recipe(base_recipes)
            
            # For each substitution recipe, calculate relevance score
            for recipe in substitution_recipes:
                # Calculate ingredient overlap with representative base recipe
                ingredient_similarity = calculate_ingredient_overlap(
                    representative_base.ingredients, recipe.ingredients)
                
                # Title similarity (simple check if dish type appears in title)
                title_match = 1.0 if dish_type.lower() in recipe.title.lower() else 0.5
                
                # Check if recipe explicitly mentions the substitution category
                category_match = 1.0 if recipe.has_substitution_category(substitution_category) else 0.5
                
                # Combine scores (ingredient similarity is the most important factor)
                score = (0.6 * ingredient_similarity) + (0.25 * title_match) + (0.15 * category_match)
                
                recipe_scores[recipe.id] = score
        else:
            # Without base recipes, rank based on title match and category match
            for recipe in substitution_recipes:
                title_match = 1.0 if dish_type.lower() in recipe.title.lower() else 0.5
                category_match = 1.0 if recipe.has_substitution_category(substitution_category) else 0.5
                
                score = (0.7 * title_match) + (0.3 * category_match)
                
                recipe_scores[recipe.id] = score
        
        # Add base recipes with substitution category to results
        for recipe in base_recipes:
            if recipe.has_substitution_category(substitution_category):
                recipe_scores[recipe.id] = 0.9  # High score but not perfect
        
        # Get all recipes with scores
        scored_recipes = []
        for recipe_id, score in recipe_scores.items():
            recipe = self.dataset.get_recipe(recipe_id)
            if recipe:
                scored_recipes.append((recipe, score))
        
        # Sort by score in descending order
        return sorted(scored_recipes, key=lambda x: x[1], reverse=True)
    
    def _find_representative_recipe(self, recipes: List[Recipe]) -> Recipe:
        """
        Find the most representative recipe from a list.
        
        Args:
            recipes: List of recipes
            
        Returns:
            The most representative recipe
        """
        if not recipes:
            raise ValueError("Empty recipe list")
        
        if len(recipes) == 1:
            return recipes[0]
        
        # Calculate pairwise ingredient overlap
        overlap_scores = {}
        
        for i, recipe1 in enumerate(recipes):
            overlap_scores[recipe1.id] = 0
            
            for j, recipe2 in enumerate(recipes):
                if i != j:
                    overlap = calculate_ingredient_overlap(recipe1.ingredients, recipe2.ingredients)
                    overlap_scores[recipe1.id] += overlap
        
        # Find recipe with highest total overlap
        best_recipe_id = max(overlap_scores.items(), key=lambda x: x[1])[0]
        
        for recipe in recipes:
            if recipe.id == best_recipe_id:
                return recipe
        
        # Fallback - should never reach here
        return recipes[0]
    
    def get_annotation_for_result(self, query: str, recipe: Recipe) -> Optional[int]:
        """
        Get annotation score for a recipe and query if one exists.
        
        Args:
            query: Search query
            recipe: Recipe object
            
        Returns:
            Annotation score (0, 1, 2) or None if no annotation exists
        """
        annotations = self.dataset.get_annotations_for_query(query)
        return annotations.get(recipe.id)


class SubstitutionSearchEngine(RecipeSearchEngine):
    """
    Enhanced search engine that specifically focuses on ingredient substitutions.
    """
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[Recipe, float]]:
        """
        Search for recipes with successful substitutions matching a query.
        
        Args:
            query: User search query (e.g., "vegetarian pad thai")
            top_k: Number of top results to return
            
        Returns:
            List of (recipe, score) tuples
        """
        # Get basic search results from parent class
        basic_results = super().search(query, top_k=top_k*2)  # Get more results to refine
        
        # Parse query
        substitution_category, dish_type = self.parse_query(query)
        
        # If no substitution category, just return basic results
        if not substitution_category:
            return basic_results[:top_k]
        
        # Rerank results based on substitution analysis
        reranked_results = []
        
        # Find original (non-substitution) recipes for comparison
        original_recipes = []
        for recipe in self.dataset.search_by_title(dish_type):
            if not recipe.has_substitution_category(substitution_category):
                original_recipes.append(recipe)
        
        # If we have original recipes to compare against
        if original_recipes:
            representative_original = self._find_representative_recipe(original_recipes)
            
            for recipe, basic_score in basic_results:
                # Skip recipes that don't match the substitution category
                if not recipe.has_substitution_category(substitution_category):
                    continue
                
                # Calculate ingredient-level substitution score
                substitution_score = self._calculate_substitution_score(
                    representative_original, recipe, substitution_category)
                
                # Combine with basic score (weighted)
                final_score = (0.4 * basic_score) + (0.6 * substitution_score)
                
                reranked_results.append((recipe, final_score))
        else:
            # Without original recipes, just filter for the substitution category
            for recipe, score in basic_results:
                if recipe.has_substitution_category(substitution_category):
                    reranked_results.append((recipe, score))
        
        # Sort by score and return top_k results
        return sorted(reranked_results, key=lambda x: x[1], reverse=True)[:top_k]
    
    def _calculate_substitution_score(self, 
                                    original_recipe: Recipe, 
                                    substitution_recipe: Recipe,
                                    substitution_category: str) -> float:
        """
        Calculate how well a recipe implements a substitution.
        
        Args:
            original_recipe: Original recipe (non-substitution)
            substitution_recipe: Recipe with substitution
            substitution_category: Type of substitution
            
        Returns:
            Score between 0 and 1
        """
        # Get normalized ingredients for both recipes
        original_ingredients = original_recipe.get_normalized_ingredients()
        substitution_ingredients = substitution_recipe.get_normalized_ingredients()
        
        # Calculate base similarity between recipes
        common_ingredients = original_ingredients.intersection(substitution_ingredients)
        similarity_score = len(common_ingredients) / max(1, len(original_ingredients))
        
        # Find ingredients in original that would need substitution
        ingredients_to_substitute = set()
        
        if substitution_category == "vegetarian":
            meat_terms = ["chicken", "beef", "pork", "fish", "shrimp", "meat"]
            for ingredient in original_ingredients:
                if any(meat in ingredient for meat in meat_terms):
                    ingredients_to_substitute.add(ingredient)
        
        elif substitution_category == "vegan":
            animal_terms = ["chicken", "beef", "pork", "fish", "shrimp", "meat", 
                          "egg", "milk", "butter", "cheese", "cream", "yogurt", "honey"]
            for ingredient in original_ingredients:
                if any(animal in ingredient for animal in animal_terms):
                    ingredients_to_substitute.add(ingredient)
        
        elif substitution_category == "gluten-free":
            gluten_terms = ["flour", "wheat", "pasta", "bread", "couscous", "barley", "rye"]
            for ingredient in original_ingredients:
                if any(gluten in ingredient for gluten in gluten_terms):
                    ingredients_to_substitute.add(ingredient)
        
        elif substitution_category == "dairy-free":
            dairy_terms = ["milk", "cheese", "butter", "cream", "yogurt"]
            for ingredient in original_ingredients:
                if any(dairy in ingredient for dairy in dairy_terms):
                    ingredients_to_substitute.add(ingredient)
        
        elif substitution_category == "nut-free":
            nut_terms = ["almond", "walnut", "pecan", "cashew", "pistachio", "nut"]
            for ingredient in original_ingredients:
                if any(nut in ingredient for nut in nut_terms):
                    ingredients_to_substitute.add(ingredient)
        
        # For other categories, use a simpler approach
        else:
            category_base = substitution_category.replace("-free", "").replace("low-", "")
            for ingredient in original_ingredients:
                if category_base in ingredient:
                    ingredients_to_substitute.add(ingredient)
        
        # Check if substitutions have been made properly
        substitution_score = 0.0
        
        if ingredients_to_substitute:
            # Get all possible substitutions for the ingredients
            all_substitutes = set()
            for ingredient in ingredients_to_substitute:
                subs = self.substitution_db.get_substitutions(ingredient, substitution_category)
                all_substitutes.update(subs)
            
            # Check if substitution recipe contains appropriate substitutes
            found_substitutes = 0
            for sub_ingredient in substitution_ingredients:
                if not sub_ingredient in original_ingredients:
                    # Check if this ingredient is one of our known substitutes
                    if any(substitute in sub_ingredient for substitute in all_substitutes):
                        found_substitutes += 1
            
            # Calculate substitution score
            if all_substitutes:
                substitution_score = min(1.0, found_substitutes / len(ingredients_to_substitute))
        else:
            # If no ingredients need substitution, score is 0
            substitution_score = 0.0
        
        # Combine similarity and substitution scores
        # Weight substitution score higher because it's the main focus
        final_score = (0.4 * similarity_score) + (0.6 * substitution_score)
        
        return final_score 