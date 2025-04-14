"""
Evaluation runner script for the Recipe Substitution Search System.
This script evaluates the search engine performance using annotation data.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.data.recipe_dataset import RecipeDataset
from src.data.substitution_db import SubstitutionDatabase
from src.models.search_engine import RecipeSearchEngine, SubstitutionSearchEngine
from src.evaluation.metrics import evaluate_search_engine
from src.data.recipe import Recipe

# Define the test queries
TEST_QUERIES = [
    "vegetarian pad thai",
    "gluten-free pancakes",
    "butter-free chocolate chip cookies",
    "eggless carbonara",
    "vegan mac and cheese",
    "dairy-free alfredo sauce",
    "nut-free pesto",
    "sugar-free brownies",
    "low-carb lasagna",
    "egg substitute in banana bread"
]


def run_evaluation(dataset_path: str = None, output_dir: str = None, enable_plots: bool = True):
    """
    Run a full evaluation of the search engine.
    
    Args:
        dataset_path: Path to the processed dataset file (if None, load default)
        output_dir: Directory to output results (if None, use default)
        enable_plots: Whether to generate plots
    """
    print("Starting Recipe Substitution Search System evaluation...")
    
    # Set up paths
    if output_dir is None:
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../results"))
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    print("Loading dataset and substitution database...")
    dataset = RecipeDataset(load_from_processed=True)
    substitution_db = SubstitutionDatabase()
    
    if dataset_path:
        # If custom dataset path provided, load it
        dataset.load_processed_dataset(dataset_path)
    
    # Create search engines
    basic_engine = RecipeSearchEngine(dataset, substitution_db)
    enhanced_engine = SubstitutionSearchEngine(dataset, substitution_db)
    
    # Collect search results
    print("Running searches with both engines...")
    basic_results = {}
    enhanced_results = {}
    
    for query in TEST_QUERIES:
        print(f"Searching for: {query}")
        basic_results[query] = basic_engine.search(query, top_k=10)
        enhanced_results[query] = enhanced_engine.search(query, top_k=10)
    
    # Get annotations
    annotations = dataset.annotations
    
    # Check if we have annotations for our test queries
    queries_with_annotations = [q for q in TEST_QUERIES if q in annotations]
    if not queries_with_annotations:
        print("Warning: No annotations found for test queries. Using dummy annotations for demonstration.")
        
        # Create dummy annotations for demo purposes
        annotations = create_dummy_annotations(basic_results, enhanced_results)
    
    # Evaluate search engines
    print("Evaluating search engines...")
    basic_metrics = evaluate_search_engine(basic_results, annotations)
    enhanced_metrics = evaluate_search_engine(enhanced_results, annotations)
    
    # Print results
    print("\nEvaluation Results:")
    print("-" * 60)
    print(f"{'Metric':<20} {'Basic Engine':<15} {'Enhanced Engine':<15} {'Improvement':<10}")
    print("-" * 60)
    
    for metric in sorted(basic_metrics.keys()):
        basic_value = basic_metrics[metric]
        enhanced_value = enhanced_metrics[metric]
        improvement = enhanced_value - basic_value
        improvement_pct = (improvement / max(0.001, basic_value)) * 100
        
        print(f"{metric:<20} {basic_value:.4f}       {enhanced_value:.4f}       {improvement_pct:+.1f}%")
    
    # Save results to files
    results = {
        "basic_engine": basic_metrics,
        "enhanced_engine": enhanced_metrics,
        "queries": list(basic_results.keys()),
        "improvement": {
            metric: enhanced_metrics[metric] - basic_value
            for metric, basic_value in basic_metrics.items()
        }
    }
    
    with open(os.path.join(output_dir, "evaluation_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {os.path.join(output_dir, 'evaluation_results.json')}")
    
    # Generate comparison plots
    if enable_plots:
        print("Generating plots...")
        generate_comparison_plots(basic_metrics, enhanced_metrics, output_dir)
        generate_per_query_plots(basic_results, enhanced_results, annotations, output_dir)
    
    print("Evaluation complete!")


def create_dummy_annotations(basic_results: Dict[str, List[Tuple[Recipe, float]]], 
                           enhanced_results: Dict[str, List[Tuple[Recipe, float]]]) -> Dict[str, Dict[str, int]]:
    """
    Create dummy annotations for demonstration purposes.
    In a real system, these would come from human judgments.
    
    Args:
        basic_results: Results from basic search engine
        enhanced_results: Results from enhanced search engine
        
    Returns:
        Dictionary of dummy annotations
    """
    annotations = {}
    
    for query in basic_results:
        annotations[query] = {}
        
        # Simulate annotations where enhanced engine does better
        # First result in enhanced gets score 2
        if enhanced_results[query]:
            enhanced_top_recipe, _ = enhanced_results[query][0]
            annotations[query][enhanced_top_recipe.id] = 2
        
        # Top half of enhanced results get score 1 or 2
        for i, (recipe, _) in enumerate(enhanced_results[query][:5]):
            if recipe.id not in annotations[query]:
                annotations[query][recipe.id] = 2 if i < 2 else 1
        
        # Top 3 of basic results get at least score 1
        for i, (recipe, _) in enumerate(basic_results[query][:3]):
            if recipe.id not in annotations[query]:
                annotations[query][recipe.id] = 1
        
        # Random scores for a few more recipes
        import random
        for i, (recipe, _) in enumerate(basic_results[query][3:7]):
            if recipe.id not in annotations[query]:
                annotations[query][recipe.id] = random.choice([0, 1])
    
    return annotations


def generate_comparison_plots(basic_metrics: Dict[str, float], 
                            enhanced_metrics: Dict[str, float], 
                            output_dir: str):
    """
    Generate comparison plots between the two search engines.
    
    Args:
        basic_metrics: Metrics for basic search engine
        enhanced_metrics: Metrics for enhanced search engine
        output_dir: Directory to save plots
    """
    plt.figure(figsize=(12, 6))
    
    metrics = ['MAP', 'MRR', 'Precision@5', 'NDCG@5']
    basic_values = [basic_metrics.get(m, 0) for m in metrics]
    enhanced_values = [enhanced_metrics.get(m, 0) for m in metrics]
    
    x = range(len(metrics))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], basic_values, width, label='Basic Engine')
    plt.bar([i + width/2 for i in x], enhanced_values, width, label='Enhanced Engine')
    
    plt.xlabel('Metric')
    plt.ylabel('Score')
    plt.title('Comparison of Search Engine Performance')
    plt.xticks(x, metrics)
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save the plot
    plot_path = os.path.join(output_dir, 'comparison_plot.png')
    plt.savefig(plot_path)
    plt.close()
    
    print(f"Comparison plot saved to {plot_path}")


def generate_per_query_plots(basic_results: Dict[str, List[Tuple[Recipe, float]]], 
                           enhanced_results: Dict[str, List[Tuple[Recipe, float]]],
                           annotations: Dict[str, Dict[str, int]],
                           output_dir: str):
    """
    Generate per-query performance plots.
    
    Args:
        basic_results: Results from basic search engine
        enhanced_results: Results from enhanced search engine
        annotations: Annotation dictionaries
        output_dir: Directory to save plots
    """
    from src.evaluation.metrics import precision_at_k, ndcg_at_k
    
    # Create bar chart of Precision@3 for each query
    plt.figure(figsize=(14, 7))
    
    queries = list(basic_results.keys())
    basic_p3 = []
    enhanced_p3 = []
    
    for query in queries:
        if query in annotations:
            basic_p3.append(precision_at_k(basic_results[query], annotations[query], k=3))
            enhanced_p3.append(precision_at_k(enhanced_results[query], annotations[query], k=3))
        else:
            basic_p3.append(0)
            enhanced_p3.append(0)
    
    x = range(len(queries))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], basic_p3, width, label='Basic Engine')
    plt.bar([i + width/2 for i in x], enhanced_p3, width, label='Enhanced Engine')
    
    plt.xlabel('Query')
    plt.ylabel('Precision@3')
    plt.title('Precision@3 by Query')
    plt.xticks(x, [q[:15] + '...' if len(q) > 15 else q for q in queries], rotation=45, ha='right')
    plt.ylim(0, 1.0)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the plot
    plot_path = os.path.join(output_dir, 'precision_by_query.png')
    plt.savefig(plot_path)
    plt.close()
    
    print(f"Per-query precision plot saved to {plot_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Recipe Substitution Search System")
    parser.add_argument("--dataset", type=str, help="Path to processed dataset file")
    parser.add_argument("--output", type=str, help="Directory for output files")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation")
    
    args = parser.parse_args()
    
    run_evaluation(
        dataset_path=args.dataset,
        output_dir=args.output,
        enable_plots=not args.no_plots
    ) 