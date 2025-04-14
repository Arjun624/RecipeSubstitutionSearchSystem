# Recipe Substitution Search System Notebooks

This directory contains Jupyter notebooks for demonstrating and analyzing the Recipe Substitution Search System.

## Setup

To use these notebooks, you'll need Jupyter installed. If you haven't already, install it with:

```bash
pip install jupyter notebook
```

## Available Notebooks

- `recipe_search_demo.ipynb`: Demonstrates core functionality of the search system
  - Shows how to load the dataset
  - Performs searches with both basic and enhanced search engines
  - Displays search results and annotations

## Running the Notebooks

From the project root directory, run:

```bash
jupyter notebook notebooks/recipe_search_demo.ipynb
```

Or to start the Jupyter server in the notebooks directory:

```bash
cd notebooks
jupyter notebook
```

## Note

If you prefer not to use Jupyter, you can still test the system using the command-line interface:

```bash
python run.py search "vegetarian pad thai"
``` 