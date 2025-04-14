# Recipe Substitution Search System

An information retrieval project focused on finding recipes that successfully incorporate specific substitutions while maintaining the essence of the original dish.

## Project Overview

Unlike standard recipe search engines that may return loosely related results when searching for substitution-based recipes (e.g., "vegetarian pad thai" returning generic noodle dishes), our system focuses on finding variations that preserve the core characteristics of the original recipe while accommodating dietary restrictions or ingredient substitutions.

The system specializes in queries like:
- "Vegetarian Pad Thai"
- "Gluten-free Pancakes"
- "Dairy-free Alfredo Sauce"
- "Vegan Mac and Cheese"
- "Nut-free Pesto"

## Features

- **Substitution-aware search**: Understands dietary restrictions and finds recipes that properly implement substitutions
- **Ingredient substitution database**: Comprehensive database of ingredient substitutions for various dietary restrictions
- **LLM integration**: Optional use of Llama 3.1 to generate high-quality ingredient substitutions
- **Relevance judging**: 0-2 scale annotation system for measuring relevance of search results
- **Evaluation system**: Detailed evaluation metrics (MAP, MRR, Precision@k) to measure search quality
- **Command-line interface**: Easy-to-use CLI for searching recipes and analyzing results

## Grade Contract Achievements

### B (Baseline)
- ✅ Collected and cleaned recipe samples covering common substitution queries
- ✅ Created and applied 0-2 relevance judgment scale
- ✅ Built substitution database for common ingredient swaps
- ✅ Implemented basic ingredient matching using Jaccard similarity
- ✅ Developed search scripts that can take a query and return recipes
- ✅ End-to-end example queries with annotations included

### B+ (B plus these)
- ✅ Expanded dataset to include diverse substitutions
- ✅ Improved ingredient matching to recognize similar ingredients
- ✅ Added command-line interface for the search tool
- ✅ Comparison capabilities between basic search and enhanced search

### A- (B+ plus these)
- ✅ Integrated LLM-based substitution generation with Llama 3.1
- ✅ Added simple analysis of recipe types in query parsing
- ✅ Created evaluation metrics (MAP, MRR, Precision@k)
- ✅ Demonstrated measurable improvement over baseline search

### A (A- plus these)
- ✅ Implemented ranking algorithm based on annotations and substitution quality
- ✅ Expanded annotation infrastructure for recipe evaluation
- ✅ Comprehensive code organization and documentation
- ✅ Demonstrated measurable improvement through evaluation metrics

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/recipe-substitution-search.git
   cd recipe-substitution-search
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) If you want to use LLM for substitution generation:
   - Download a Llama model as described in the `models/README.md` file
   - For GPU acceleration: `pip install llama-cpp-python-cuda-11` (for CUDA 11.x)

4. Initialize the system with demo data:
   ```bash
   python run.py init
   ```

## Usage

### Command Line Interface

The system provides a comprehensive command-line interface with various commands:

#### 1. Initialization Command

```bash
python run.py init
```
- Creates necessary directories if they don't exist
- Generates demo recipes and example annotations
- Creates a substitution database with ingredient mappings
- Generates additional dummy recipes for testing

Options:
- `--force`: Force reset the system by deleting existing data
- `--count NUMBER`: Specify number of dummy recipes to create (default: 50)

#### 2. Search Commands

```bash
# Direct search with query
python run.py search "vegetarian pad thai"

# Interactive search mode
python run.py search
```

Search options:
- `--basic`: Use the basic search engine instead of enhanced
- `--results NUMBER`: Number of results to display (default: 5)
- `--details`: Show full recipe details including complete instructions

#### 3. Evaluation Command

```bash
python run.py evaluate
```
- Runs a complete evaluation of the search system
- Compares basic and enhanced search engines
- Calculates metrics like MAP, MRR, Precision@k
- Generates visualization charts

Options:
- `--no-plots`: Disable generation of performance plots
- `--output DIRECTORY`: Specify directory for output files

#### 4. Data Collection Commands

```bash
# Collect recipe data (interactive mode)
python run.py collect

# Add annotations for search results
python run.py annotate --query "gluten-free pancakes"

# Generate dummy recipes
python run.py generate --count 50
```

### Interactive Mode Commands

When running `python run.py search` in interactive mode, you can use these commands:

- `help`: Display available commands
- `queries`: List all annotated queries in the system
- `stats`: Show dataset statistics (recipes, annotations, etc.)
- `exit`: Exit the program
- Any text not matching these commands is treated as a search query

### Example Workflows

#### Basic Search Workflow:
```bash
# Initialize the system
python run.py init

# Search for vegetarian recipes
python run.py search "vegetarian pad thai"

# Compare with basic search engine
python run.py search "vegetarian pad thai" --basic
```

#### Evaluation Workflow:
```bash
# Run the evaluation
python run.py evaluate

# Check the results
cat results/evaluation_results.json
```

#### Annotation Workflow:
```bash
# Search for recipes
python run.py search "gluten-free pancakes"

# Add annotations
python run.py annotate --query "gluten-free pancakes"

# Re-run evaluation to see improvements
python run.py evaluate
```

### Programmatic Usage

You can also use the system programmatically:

```python
from src.data.recipe_dataset import RecipeDataset
from src.data.substitution_db import SubstitutionDatabase
from src.models.search_engine import SubstitutionSearchEngine

# Initialize
dataset = RecipeDataset()
substitution_db = SubstitutionDatabase()
search_engine = SubstitutionSearchEngine(dataset, substitution_db)

# Search for recipes
results = search_engine.search("vegetarian pad thai", top_k=5)

# Display results
for recipe, score in results:
    print(f"{recipe.title} (Score: {score:.2f})")
    print(f"Diet labels: {recipe.diet_labels}")
    print(f"Ingredients: {len(recipe.ingredients)} items")
    print("-" * 40)
```

## Project Structure

```
.
├── data/                  # Data storage
│   ├── raw/               # Raw recipe data
│   ├── processed/         # Processed data and substitution databases
│   └── annotations/       # Human annotations
├── models/                # LLM models for substitution generation
├── notebooks/             # Jupyter notebooks for analysis and demos
├── scripts/               # Utility scripts
├── src/                   # Source code
│   ├── data/              # Data processing modules
│   ├── evaluation/        # Evaluation metrics and testing
│   ├── models/            # Search engines and ranking algorithms
│   └── utils/             # Helper functions and configuration
├── run.py                 # Main entry point for running commands
└── requirements.txt       # Project dependencies
```

## Annotation System

Recipes are annotated on a 0-2 scale for each query:

- **0 points**: Recipes that miss the mark - don't successfully achieve the substitution goal or completely lose the essence of the original dish.
- **1 point**: Okay matches - make the requested substitution but lose something in translation (like gluten-free pancakes with a slightly compromised texture).
- **2 points**: Great matches - successfully nail both the substitution requirement and maintain the original dish's essence.

## Evaluation

The system is evaluated using standard information retrieval metrics:

- **Mean Average Precision (MAP)**: Measures the average precision across all relevant documents
- **Mean Reciprocal Rank (MRR)**: Measures how high the first relevant result appears
- **Precision@k**: Measures the proportion of relevant results in the top-k positions

## Future Improvements

- Expand the dataset with more real-world recipes
- Improve ingredient parsing to handle more complex descriptions
- Implement a web interface for easier interaction
- Add more sophisticated ranking algorithms based on user feedback
- Include cooking method analysis to better assess recipe similarity

## Contributors

- Arjun Avinash
- Ahaan Chaudhuri

