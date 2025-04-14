"""
Recipe data class module for the Recipe Substitution Search System.
This module defines the Recipe class used to represent recipes throughout the system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

import json
import re
from pathlib import Path

from src.utils.recipe_utils import normalize_ingredient, extract_ingredients


@dataclass
class Recipe:
    """
    Class representing a recipe with its attributes and methods.
    """
    id: str
    title: str
    ingredients: List[str]
    instructions: str
    url: Optional[str] = None
    cuisine: Optional[str] = None
    diet_labels: List[str] = field(default_factory=list)
    cooking_time: Optional[int] = None
    serving_size: Optional[int] = None
    nutrition: Optional[Dict] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Recipe":
        """
        Create a Recipe object from a dictionary.
        
        Args:
            data: Dictionary containing recipe data
        
        Returns:
            Recipe object
        """
        required_fields = {"id", "title", "ingredients", "instructions"}
        if not all(field in data for field in required_fields):
            missing = required_fields - set(data.keys())
            raise ValueError(f"Missing required fields: {missing}")
        
        # Convert ingredients to a list if it's a string
        if isinstance(data.get("ingredients", ""), str):
            data["ingredients"] = extract_ingredients(data["ingredients"])
        
        # Create Recipe object with all available fields
        return cls(
            id=data["id"],
            title=data["title"],
            ingredients=data["ingredients"],
            instructions=data["instructions"],
            url=data.get("url"),
            cuisine=data.get("cuisine"),
            diet_labels=data.get("diet_labels", []),
            cooking_time=data.get("cooking_time"),
            serving_size=data.get("serving_size"),
            nutrition=data.get("nutrition"),
            image_url=data.get("image_url"),
            source=data.get("source"),
            tags=data.get("tags", [])
        )
    
    def to_dict(self) -> Dict:
        """
        Convert Recipe object to a dictionary.
        
        Returns:
            Dictionary representation of the recipe
        """
        return {
            "id": self.id,
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "url": self.url,
            "cuisine": self.cuisine,
            "diet_labels": self.diet_labels,
            "cooking_time": self.cooking_time,
            "serving_size": self.serving_size,
            "nutrition": self.nutrition,
            "image_url": self.image_url,
            "source": self.source,
            "tags": self.tags
        }
    
    def get_normalized_ingredients(self) -> Set[str]:
        """
        Get normalized ingredients for comparison.
        
        Returns:
            Set of normalized ingredient names
        """
        return {normalize_ingredient(ing) for ing in self.ingredients if normalize_ingredient(ing)}
    
    def has_ingredient(self, ingredient: str) -> bool:
        """
        Check if recipe contains a specific ingredient.
        
        Args:
            ingredient: Ingredient to check for
            
        Returns:
            Boolean indicating if ingredient is present
        """
        norm_ingredient = normalize_ingredient(ingredient)
        if not norm_ingredient:
            return False
        
        norm_recipe_ingredients = self.get_normalized_ingredients()
        
        # Check for exact match
        if norm_ingredient in norm_recipe_ingredients:
            return True
        
        # Check for partial match (e.g., "chicken broth" should match if we're looking for "chicken")
        for ing in norm_recipe_ingredients:
            if norm_ingredient in ing or ing in norm_ingredient:
                return True
        
        return False
    
    def has_substitution_category(self, category: str) -> bool:
        """
        Check if recipe matches a substitution category.
        
        Args:
            category: Substitution category to check
            
        Returns:
            Boolean indicating if recipe matches category
        """
        # Convert to lowercase for case-insensitive matching
        category_lower = category.lower()
        
        # Check diet labels and tags
        for label in self.diet_labels:
            if category_lower in label.lower():
                return True
        
        for tag in self.tags:
            if category_lower in tag.lower():
                return True
        
        # Check title for category
        if category_lower in self.title.lower():
            return True
        
        return False
    
    def __str__(self) -> str:
        """String representation of the recipe."""
        return f"Recipe: {self.title} ({len(self.ingredients)} ingredients)" 