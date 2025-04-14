"""
Configuration settings for the Recipe Substitution Search System.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ANNOTATIONS_DIR = DATA_DIR / "annotations"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Substitution categories to focus on
SUBSTITUTION_CATEGORIES = [
    "vegetarian",
    "vegan",
    "gluten-free",
    "dairy-free",
    "nut-free"
]

# Annotation scores
ANNOTATION_SCORES = {
    0: "Misses the mark - doesn't achieve substitution goal or loses dish essence",
    1: "Okay match - makes substitution but loses something in translation",
    2: "Great match - nails substitution requirement and maintains dish essence"
}

# Evaluation metrics
EVALUATION_METRICS = ["MAP", "MRR", "precision@k"]

# LLM settings (for substitution mapping generation)
USE_LLM = True
LLM_MODEL_PATH = MODELS_DIR / "llama-3.1-8b-instruct.Q4_K_M.gguf"  # Update with actual model path 