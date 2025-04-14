"""
Evaluation metrics module for the Recipe Substitution Search System.
This module implements information retrieval metrics to evaluate 
the performance of the search engine.
"""

from typing import Dict, List, Optional, Set, Tuple, Union
import numpy as np

from src.data.recipe import Recipe


def precision_at_k(results: List[Tuple[Recipe, float]], 
                 annotations: Dict[str, int], 
                 k: int = 5, 
                 relevant_threshold: int = 1) -> float:
    """
    Calculate Precision@K metric.
    
    Args:
        results: List of (recipe, score) tuples from search
        annotations: Dictionary mapping recipe IDs to relevance scores
        k: The k in Precision@K
        relevant_threshold: Minimum annotation score to be considered relevant
        
    Returns:
        Precision@K score (0-1)
    """
    # If no results, precision is 0
    if not results:
        return 0.0
    
    # Limit to top-k results
    results = results[:k]
    
    # Count relevant results
    relevant_count = 0
    for recipe, _ in results:
        annotation = annotations.get(recipe.id)
        if annotation is not None and annotation >= relevant_threshold:
            relevant_count += 1
    
    # Calculate precision
    return relevant_count / min(k, len(results))


def average_precision(results: List[Tuple[Recipe, float]], 
                     annotations: Dict[str, int],
                     relevant_threshold: int = 1) -> float:
    """
    Calculate Average Precision for a single query.
    
    Args:
        results: List of (recipe, score) tuples from search
        annotations: Dictionary mapping recipe IDs to relevance scores
        relevant_threshold: Minimum annotation score to be considered relevant
        
    Returns:
        Average Precision score (0-1)
    """
    # If no results or no relevant annotations, AP is 0
    if not results or not any(score >= relevant_threshold for score in annotations.values()):
        return 0.0
    
    # Count total relevant items in annotations
    total_relevant = sum(1 for score in annotations.values() if score >= relevant_threshold)
    
    # If no relevant items, AP is 0
    if total_relevant == 0:
        return 0.0
    
    # Calculate sum of precisions at relevant positions
    cumulative_precision = 0.0
    relevant_seen = 0
    
    for i, (recipe, _) in enumerate(results):
        # Check if current result is relevant
        annotation = annotations.get(recipe.id)
        is_relevant = annotation is not None and annotation >= relevant_threshold
        
        if is_relevant:
            relevant_seen += 1
            # Add precision at this position
            precision_at_i = relevant_seen / (i + 1)
            cumulative_precision += precision_at_i
    
    # Calculate AP
    return cumulative_precision / total_relevant


def mean_average_precision(query_results: Dict[str, List[Tuple[Recipe, float]]],
                         annotations: Dict[str, Dict[str, int]],
                         relevant_threshold: int = 1) -> float:
    """
    Calculate Mean Average Precision across multiple queries.
    
    Args:
        query_results: Dictionary mapping queries to search results
        annotations: Dictionary mapping queries to annotation dictionaries
        relevant_threshold: Minimum annotation score to be considered relevant
        
    Returns:
        MAP score (0-1)
    """
    # If no queries, MAP is 0
    if not query_results:
        return 0.0
    
    # Calculate AP for each query
    ap_scores = []
    
    for query, results in query_results.items():
        # Skip queries without annotations
        if query not in annotations:
            continue
            
        query_annotations = annotations[query]
        ap = average_precision(results, query_annotations, relevant_threshold)
        ap_scores.append(ap)
    
    # Calculate MAP
    if not ap_scores:
        return 0.0
        
    return sum(ap_scores) / len(ap_scores)


def reciprocal_rank(results: List[Tuple[Recipe, float]], 
                  annotations: Dict[str, int],
                  relevant_threshold: int = 1) -> float:
    """
    Calculate Reciprocal Rank for a single query.
    
    Args:
        results: List of (recipe, score) tuples from search
        annotations: Dictionary mapping recipe IDs to relevance scores
        relevant_threshold: Minimum annotation score to be considered relevant
        
    Returns:
        Reciprocal Rank score (0-1)
    """
    # If no results, RR is 0
    if not results:
        return 0.0
    
    # Find position of first relevant result
    for i, (recipe, _) in enumerate(results):
        annotation = annotations.get(recipe.id)
        if annotation is not None and annotation >= relevant_threshold:
            return 1.0 / (i + 1)  # Reciprocal of 1-based rank
    
    # If no relevant result found, RR is 0
    return 0.0


def mean_reciprocal_rank(query_results: Dict[str, List[Tuple[Recipe, float]]],
                        annotations: Dict[str, Dict[str, int]],
                        relevant_threshold: int = 1) -> float:
    """
    Calculate Mean Reciprocal Rank across multiple queries.
    
    Args:
        query_results: Dictionary mapping queries to search results
        annotations: Dictionary mapping queries to annotation dictionaries
        relevant_threshold: Minimum annotation score to be considered relevant
        
    Returns:
        MRR score (0-1)
    """
    # If no queries, MRR is 0
    if not query_results:
        return 0.0
    
    # Calculate RR for each query
    rr_scores = []
    
    for query, results in query_results.items():
        # Skip queries without annotations
        if query not in annotations:
            continue
            
        query_annotations = annotations[query]
        rr = reciprocal_rank(results, query_annotations, relevant_threshold)
        rr_scores.append(rr)
    
    # Calculate MRR
    if not rr_scores:
        return 0.0
        
    return sum(rr_scores) / len(rr_scores)


def ndcg_at_k(results: List[Tuple[Recipe, float]], 
             annotations: Dict[str, int], 
             k: int = 10) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at K.
    This metric takes into account the graded relevance of the results.
    
    Args:
        results: List of (recipe, score) tuples from search
        annotations: Dictionary mapping recipe IDs to relevance scores
        k: The k in NDCG@K
        
    Returns:
        NDCG@K score (0-1)
    """
    # If no results, NDCG is 0
    if not results:
        return 0.0
    
    # Limit to top-k results
    results = results[:k]
    
    # Calculate DCG
    dcg = 0.0
    for i, (recipe, _) in enumerate(results):
        # Get relevance score (0-2)
        rel = annotations.get(recipe.id, 0)
        # Use 2^rel - 1 for graded relevance
        gain = (2 ** rel) - 1
        # Discount by log_2(i+2) to account for position (1-indexed)
        dcg += gain / np.log2(i + 2)
    
    # Calculate ideal DCG
    # Get all relevance scores and sort in descending order
    ideal_rel = sorted([score for score in annotations.values()], reverse=True)
    
    # If no relevant items, ideal DCG is 0
    if not ideal_rel or max(ideal_rel) == 0:
        return 0.0
    
    # Calculate ideal DCG with perfectly ordered results
    idcg = 0.0
    for i in range(min(k, len(ideal_rel))):
        gain = (2 ** ideal_rel[i]) - 1
        idcg += gain / np.log2(i + 2)
    
    # If ideal DCG is 0, NDCG is 0
    if idcg == 0:
        return 0.0
    
    # Calculate NDCG
    return dcg / idcg


def evaluate_search_engine(search_results: Dict[str, List[Tuple[Recipe, float]]],
                         annotations: Dict[str, Dict[str, int]],
                         k_values: List[int] = [5, 10]) -> Dict[str, float]:
    """
    Evaluate a search engine using multiple metrics.
    
    Args:
        search_results: Dictionary mapping queries to search results
        annotations: Dictionary mapping queries to annotation dictionaries
        k_values: List of k values for Precision@K and NDCG@K
        
    Returns:
        Dictionary of evaluation metrics
    """
    metrics = {}
    
    # Calculate MAP
    metrics["MAP"] = mean_average_precision(search_results, annotations)
    
    # Calculate MRR
    metrics["MRR"] = mean_reciprocal_rank(search_results, annotations)
    
    # Calculate Precision@K and NDCG@K for each k
    for k in k_values:
        # Average Precision@K across queries
        p_at_k_values = []
        for query, results in search_results.items():
            if query in annotations:
                p_at_k = precision_at_k(results, annotations[query], k=k)
                p_at_k_values.append(p_at_k)
        
        if p_at_k_values:
            metrics[f"Precision@{k}"] = sum(p_at_k_values) / len(p_at_k_values)
        else:
            metrics[f"Precision@{k}"] = 0.0
        
        # Average NDCG@K across queries
        ndcg_values = []
        for query, results in search_results.items():
            if query in annotations:
                ndcg = ndcg_at_k(results, annotations[query], k=k)
                ndcg_values.append(ndcg)
        
        if ndcg_values:
            metrics[f"NDCG@{k}"] = sum(ndcg_values) / len(ndcg_values)
        else:
            metrics[f"NDCG@{k}"] = 0.0
    
    return metrics 