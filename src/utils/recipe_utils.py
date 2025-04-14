"""
Utility functions for processing and handling recipe data.
"""

import re
import string
from typing import Dict, List, Set, Tuple, Union

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Common cooking units to normalize
UNITS = {
    'tablespoon': ['tbsp', 'tbs', 'tablespoon', 'tablespoons'],
    'teaspoon': ['tsp', 'teaspoon', 'teaspoons'],
    'cup': ['cup', 'cups', 'c'],
    'ounce': ['oz', 'ounce', 'ounces'],
    'pound': ['lb', 'pound', 'pounds'],
    'gram': ['g', 'gram', 'grams'],
    'kilogram': ['kg', 'kilogram', 'kilograms'],
    'milliliter': ['ml', 'milliliter', 'milliliters'],
    'liter': ['l', 'liter', 'liters']
}

def normalize_ingredient(ingredient: str) -> str:
    """
    Normalize an ingredient string by removing quantities, units, and preprocessing.
    
    Args:
        ingredient: Raw ingredient string (e.g., "2 tbsp olive oil")
        
    Returns:
        Normalized ingredient name (e.g., "olive oil")
    """
    # Remove quantities (numbers and fractions)
    ingredient = re.sub(r'\d+\s*\/\s*\d+', '', ingredient)  # Remove fractions like 1/2
    ingredient = re.sub(r'\d+\.\d+', '', ingredient)  # Remove decimals like 0.5
    ingredient = re.sub(r'\d+', '', ingredient)  # Remove whole numbers
    
    # Remove units
    for standard_unit, variations in UNITS.items():
        for unit in variations:
            ingredient = re.sub(r'\b' + unit + r'\b', '', ingredient)
    
    # Remove punctuation
    ingredient = ingredient.translate(str.maketrans('', '', string.punctuation))
    
    # Tokenize, remove stopwords, and lemmatize
    tokens = word_tokenize(ingredient.lower())
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    
    # Rejoin and strip extra whitespace
    return ' '.join(tokens).strip()

def extract_ingredients(recipe_text: str) -> List[str]:
    """
    Extract ingredient list from recipe text.
    This is a placeholder - in a real implementation, this would use more
    sophisticated NLP techniques or structured recipe data.
    
    Args:
        recipe_text: Full recipe text
        
    Returns:
        List of ingredients
    """
    # This is a simplified placeholder implementation
    # In a real system, this would use more sophisticated NLP or structured data
    ingredients_section = re.search(r'ingredients:(.*?)instructions:', 
                                   recipe_text.lower(), re.DOTALL)
    
    if not ingredients_section:
        return []
    
    # Split by newlines and bullet points
    raw_ingredients = re.split(r'[\n•\*-]', ingredients_section.group(1))
    
    # Clean up each ingredient
    ingredients = []
    for ingredient in raw_ingredients:
        ingredient = ingredient.strip()
        if ingredient:  # Skip empty strings
            ingredients.append(ingredient)
    
    return ingredients

def calculate_ingredient_overlap(recipe1_ingredients: List[str], 
                               recipe2_ingredients: List[str]) -> float:
    """
    Calculate the Jaccard similarity between two sets of ingredients.
    
    Args:
        recipe1_ingredients: List of ingredients from first recipe
        recipe2_ingredients: List of ingredients from second recipe
        
    Returns:
        Jaccard similarity score (0-1)
    """
    # Normalize all ingredients
    set1 = {normalize_ingredient(ing) for ing in recipe1_ingredients}
    set2 = {normalize_ingredient(ing) for ing in recipe2_ingredients}
    
    # Remove empty strings
    set1 = {ing for ing in set1 if ing}
    set2 = {ing for ing in set2 if ing}
    
    # Calculate Jaccard similarity
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def is_substitution_successful(original_recipe: Dict, 
                            variation_recipe: Dict,
                            substitution_type: str) -> bool:
    """
    Determine if a recipe variation successfully incorporates a substitution.
    
    Args:
        original_recipe: Dictionary containing original recipe data
        variation_recipe: Dictionary containing variation recipe data
        substitution_type: Type of substitution (e.g., "vegetarian", "gluten-free")
        
    Returns:
        Boolean indicating if substitution appears successful
    """
    # This is a placeholder - a real implementation would use more sophisticated logic
    # based on ingredient analysis, substitution databases, etc.
    
    # For demonstration purposes, we'll use a simple heuristic
    if substitution_type == "vegetarian":
        meat_ingredients = ["chicken", "beef", "pork", "fish", "shrimp", "meat"]
        for ingredient in original_recipe.get("ingredients", []):
            if any(meat in normalize_ingredient(ingredient) for meat in meat_ingredients):
                # Original has meat, variation should not have these ingredients
                for var_ingredient in variation_recipe.get("ingredients", []):
                    if any(meat in normalize_ingredient(var_ingredient) for meat in meat_ingredients):
                        return False
                # If we got here, no meat was found in the variation
                return True
    
    # Similar logic would be implemented for other substitution types
    
    return False  # Default fallback 